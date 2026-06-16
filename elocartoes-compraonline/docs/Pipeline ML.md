# Pipeline E2E - Fraud Detection Model Training

Guia para demonstrar o pipeline completo de re-treinamento do modelo de fraude Elo.

## Arquitetura

```
etl-delta-filter (Lambda)
  → grava Parquet em training_zone/
    → S3 Notification dispara training-launcher (Lambda)
      → lanca SageMaker Training Job
        → grava artefatos no bucket sagemaker
          → S3 Notification dispara register-best-model (Lambda)
            → registra melhor modelo no MLflow
```

Todo o pipeline e event-driven. Basta disparar a primeira Lambda.

## Pre-requisito

```bash
aws sso login --profile elo
```

---

## ETAPA 1 — Preparar os dados

Le a Delta Table, classifica registros em train/test/oot, remove colunas sensiveis e grava Parquet.

```bash
aws lambda invoke \
  --function-name elo-fraud-etl-delta-filter-dev \
  --region us-east-1 \
  --profile elo \
  --payload '{}' \
  --cli-read-timeout 900 \
  /tmp/etl-response.json \
  && python3 -m json.tool /tmp/etl-response.json
```

Resposta esperada:

```json
{
    "statusCode": 200,
    "rows_written": 99873,
    "output_path": "elo-fraud-data-processed-dev-.../training_zone/transactions_YYYYMMDDHHMMSS.parquet",
    "oot_start": "2025-07-16T15:07:05+00:00",
    "test_start": "2025-06-16T15:07:05+00:00",
    "end_date": "2025-08-16T15:07:05+00:00"
}
```

Tempo: ~30-60s | Config: 10 GB RAM, timeout 15 min

---

## ETAPA 2 — Verificar o lancamento do treinamento

O Parquet em `training_zone/` dispara automaticamente a training-launcher via S3 Notification.

```bash
aws logs tail /aws/lambda/elo-fraud-training-launcher-dev \
  --since 5m \
  --format short \
  --region us-east-1 \
  --profile elo
```

Linhas que confirmam sucesso:

```
[INFO] Training launcher invoked
[INFO] Job launched: XGBClassifier_SimpleImputer_NoApply_SMOTE
[INFO] Total jobs launched: 1
```

Tempo: ~2-3s | Config: 512 MB RAM, timeout 5 min

---

## ETAPA 3 — Acompanhar o treinamento no SageMaker

### 3a. Listar jobs recentes

```bash
aws sagemaker list-training-jobs \
  --region us-east-1 \
  --profile elo \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 3 \
  --query 'TrainingJobSummaries[*].{Nome:TrainingJobName,Status:TrainingJobStatus,Criado:CreationTime}' \
  --output table
```

Saida esperada:

```
--------------------------------------------------------------------------------------------
|                                     ListTrainingJobs                                     |
+---------------------------------+------------------------------------------+-------------+
|             Criado              |                  Nome                    |   Status    |
+---------------------------------+------------------------------------------+-------------+
|  2026-02-06T09:09:46.925000..  |  elo-fraud-model-dev-job-20260206120946  |  Completed  |
+---------------------------------+------------------------------------------+-------------+
```

### 3b. Monitorar o progresso

Substituir `<NOME-DO-JOB>` pelo nome retornado acima:

```bash
aws sagemaker describe-training-job \
  --training-job-name <NOME-DO-JOB> \
  --region us-east-1 \
  --profile elo \
  --query '{Status:TrainingJobStatus,Fase:SecondaryStatus,Duracao_Segundos:TrainingTimeInSeconds}' \
  --output table
```

Saida esperada:

```
-----------------------------------------------------
|               DescribeTrainingJob                  |
+-------------------+-------+-----------------------+
| Duracao_Segundos  | Fase  |       Status          |
+-------------------+-------+-----------------------+
|  661              | Completed | Completed          |
+-------------------+-------+-----------------------+
```

Fases em ordem: `Starting` → `Downloading` → `Training` → `Uploading` → `Completed`

Tempo total: ~11 minutos

---

## ETAPA 4 — Verificar o registro do melhor modelo

O SageMaker grava artefatos no bucket, o que dispara a register-best-model. Ela compara a metrica `f1_oot` e registra no Model Registry se for melhor.

```bash
aws logs tail /aws/lambda/elo-fraud-register-best-model-dev \
  --since 15m \
  --format short \
  --region us-east-1 \
  --profile elo
```

E normal ver varias invocacoes (uma por artefato gravado pelo SageMaker).

Tempo: ~500ms por invocacao | Config: 512 MB RAM, timeout 5 min

---

## ETAPA 5 (opcional) — Logs do container de treinamento

### 5a. Encontrar o log stream

```bash
aws logs describe-log-streams \
  --log-group-name /aws/sagemaker/TrainingJobs \
  --log-stream-name-prefix <NOME-DO-JOB> \
  --region us-east-1 \
  --profile elo \
  --query 'logStreams[*].logStreamName' \
  --output table
```

### 5b. Ler os logs

```bash
aws logs tail /aws/sagemaker/TrainingJobs \
  --log-stream-name-prefix <NOME-DO-JOB> \
  --since 15m \
  --format short \
  --region us-east-1 \
  --profile elo
```

---

## Recursos

| Recurso | Nome |
|---|---|
| Lambda ETL | `elo-fraud-etl-delta-filter-dev` |
| Lambda Launcher | `elo-fraud-training-launcher-dev` |
| Lambda Register | `elo-fraud-register-best-model-dev` |
| S3 Data Lake | `elo-fraud-data-processed-dev-888577064416` |
| S3 SageMaker | `sagemaker-us-east-1-888577064416` |
| MLflow App | `app-LNOFZM2USGXQ` |
| ECR Model | `elo-fraud-model-dev` |
| SageMaker Instance | `ml.r5.4xlarge` |
| Regiao | `us-east-1` |
