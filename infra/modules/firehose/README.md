# Firehose Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Buffer e Batching](#buffer-e-batching)
- [Particionamento S3](#particionamento-s3)
- [Monitoramento](#monitoramento)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona um **Amazon Kinesis Data Firehose Delivery Stream** para entrega em batch de dados para S3, reduzindo chamadas PUT em aproximadamente 99%.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Batch Delivery** | Acumula records e entrega em lotes para S3 |
| **Reducao de Custos** | ~99% menos chamadas S3 PUT |
| **Particionamento** | Organiza automaticamente por ano/mes/dia/hora |
| **Durabilidade** | Buffer persistente, entrega garantida |

### Por que Firehose?

| Beneficio | Descricao |
|-----------|-----------|
| **Serverless** | Escala automaticamente sem provisionar capacidade |
| **Near Real-time** | Entrega em segundos a minutos (configuravel) |
| **Integracao Nativa** | Funciona com S3, Redshift, OpenSearch, Splunk |
| **Transformacao** | Suporta Lambda para transformacao de dados |
| **Error Handling** | Logs de erro e retry automatico |

### Caso de Uso no Projeto

O Firehose recebe os resultados de transacoes processadas pelo servico `process` e entrega em batch para o S3, criando arquivos particionados por data/hora para analise posterior.

---

## Arquitetura

```
                              Fluxo de Dados
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────────────────┐  │
│   │  EKS Service  │      │   Firehose    │      │           S3              │  │
│   │   (process)   │─────▶│   Delivery    │─────▶│                           │  │
│   │               │      │    Stream     │      │  landing_zone/            │  │
│   │  put_record() │      │               │      │    year=2024/             │  │
│   └───────────────┘      │  ┌─────────┐  │      │      month=01/            │  │
│                          │  │ Buffer  │  │      │        day=15/            │  │
│                          │  │ 1MB/60s │  │      │          hour=14/         │  │
│                          │  └─────────┘  │      │            file.json      │  │
│                          │               │      │                           │  │
│                          └───────────────┘      └───────────────────────────┘  │
│                                 │                                               │
│                                 │ Error Logs                                    │
│                                 ▼                                               │
│                          ┌───────────────┐                                      │
│                          │  CloudWatch   │                                      │
│                          │    Logs       │                                      │
│                          └───────────────┘                                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Integracao no Sistema Completo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Fluxo Assincrono Completo                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Cliente ELO ──▶ SQS FIFO ──▶ EKS (process) ──┬──▶ DynamoDB (Feature Store)  │
│   (feedback)                        │          │                               │
│                                     │          └──▶ Firehose ──▶ S3 (Batch)   │
│                                     │                                          │
│                                     └──▶ Logs                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Comparativo: PUT Individual vs Firehose

```
Cenario: 10.000 transacoes/dia

SEM Firehose (PUT individual):
──────────────────────────────
10.000 PUT requests/dia x $0.000005/PUT = $0.05/dia
                                        = $1.50/mes

COM Firehose (batch):
─────────────────────
~100 arquivos/dia (10.000 / 100 records por arquivo)
100 PUT requests/dia x $0.000005/PUT = $0.0005/dia
                                     = $0.015/mes
Firehose: 10MB x $0.029/GB = ~$0.30/mes

Total: ~$0.32/mes vs $1.50/mes = 78% reducao
(Economia maior com volumes maiores)
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `firehose` | `aws_cloudwatch_log_group` | Log group para erros (7 dias) |
| `firehose_s3` | `aws_cloudwatch_log_stream` | Log stream "S3Delivery" |
| `firehose` | `aws_iam_role` | IAM Role para o Firehose |
| `firehose_s3_full_access` | `aws_iam_role_policy_attachment` | Policy S3FullAccess |
| `firehose_cloudwatch_logs` | `aws_iam_role_policy_attachment` | Policy CloudWatchLogsFullAccess |
| `main` | `aws_kinesis_firehose_delivery_stream` | Delivery stream principal |
| `delivery_to_s3` | `aws_cloudwatch_metric_alarm` | Alarme de falha (opcional) |

### IAM Role

A role possui trust policy restritiva com `sts:ExternalId`:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "firehose.amazonaws.com"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "<ACCOUNT_ID>"
      }
    }
  }]
}
```

### Policies Anexadas

| Policy | Proposito |
|--------|-----------|
| `AmazonS3FullAccess` | Escrita no bucket de destino |
| `CloudWatchLogsFullAccess` | Logs de erro de entrega |

---

## Buffer e Batching

O Firehose acumula records em um buffer antes de entregar ao S3.

### Configuracao do Buffer

| Parametro | Padrao | Descricao |
|-----------|--------|-----------|
| `buffer_size_mb` | 1 MB | Tamanho maximo antes de flush |
| `buffer_interval_seconds` | 60 s | Tempo maximo antes de flush |

### Comportamento

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Buffer Behavior                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Record 1 ──┐                                                                  │
│   Record 2 ──┼──▶ Buffer ──▶ (1MB OU 60s atingido) ──▶ Flush para S3          │
│   Record N ──┘                                                                  │
│                                                                                 │
│   Condicao de flush (o que ocorrer primeiro):                                  │
│   - Buffer atinge 1 MB                                                          │
│   - 60 segundos desde ultimo flush                                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Recomendacoes por Ambiente

| Ambiente | buffer_size_mb | buffer_interval_seconds | Motivo |
|----------|----------------|-------------------------|--------|
| **DEV** | 1 | 60 | Feedback rapido para debug |
| **STAGING** | 5 | 120 | Balanco entre latencia e custo |
| **PROD** | 10 | 300 | Otimizacao de custo |

---

## Particionamento S3

Os dados sao particionados usando formato **Hive-style**, compativel com Hadoop, Spark, Hive, Presto e AWS Glue.

### Estrutura de Prefixos

```
Dados:
{bucket}/{prefix}/year=YYYY/month=MM/day=DD/hour=HH/{file}

Erros:
{bucket}/{prefix}/errors/{error-type}/year=YYYY/month=MM/day=DD/{file}
```

### Exemplo Real

```
s3://elo-fraud-data-processed-staging-888577064416/
└── landing_zone/
    ├── year=2024/
    │   └── month=01/
    │       └── day=15/
    │           ├── hour=10/
    │           │   └── firehose-1-2024-01-15-10-00-00-abc123.json
    │           ├── hour=11/
    │           │   └── firehose-1-2024-01-15-11-00-00-def456.json
    │           └── hour=12/
    │               └── firehose-1-2024-01-15-12-00-00-ghi789.json
    └── errors/
        └── processing-failed/
            └── year=2024/
                └── month=01/
                    └── day=15/
                        └── error-file.json
```

### Beneficios do Particionamento Hive-style

| Beneficio | Descricao |
|-----------|-----------|
| **Query Performance** | Athena/Spark podem fazer partition pruning |
| **Custo Reduzido** | Queries escaneiam apenas particoes relevantes |
| **Compatibilidade** | Padrao da industria (Hadoop, Spark, Hive) |
| **Glue Crawler** | Detecta particoes automaticamente |

---

## Monitoramento

### CloudWatch Logs

Logs de erro de entrega sao salvos em:

```
/aws/kinesisfirehose/{stream_name}
└── S3Delivery
```

**Retencao**: 7 dias

### CloudWatch Alarm

Alarme opcional para falha na entrega:

| Metrica | Condicao | Periodo |
|---------|----------|---------|
| `DeliveryToS3.Success` | < 1 | 2 x 5 min |

### Metricas Disponiveis

| Metrica | Descricao |
|---------|-----------|
| `IncomingRecords` | Records recebidos |
| `IncomingBytes` | Bytes recebidos |
| `DeliveryToS3.Success` | Entregas bem-sucedidas |
| `DeliveryToS3.Records` | Records entregues ao S3 |
| `DeliveryToS3.DataFreshness` | Latencia de entrega |

---

## Uso

### Uso Basico

```hcl
module "firehose" {
  source = "../../modules/firehose"

  project_name  = "elo-fraud"
  environment   = "dev"
  stream_name   = "elo-fraud-transactions-firehose-dev"
  s3_bucket_arn = module.s3.data_processed_bucket_arn
}
```

### Uso com Configuracoes Customizadas

```hcl
module "firehose" {
  source = "../../modules/firehose"

  project_name = "elo-fraud"
  environment  = "staging"
  stream_name  = "elo-fraud-transactions-firehose-staging"

  # Descricao para tags
  purpose_description = "Transaction Results Batch Delivery"

  # S3 destination
  s3_bucket_arn = module.s3.data_processed_bucket_arn
  s3_prefix     = "landing_zone"

  # Buffer configuration
  buffer_size_mb          = 5
  buffer_interval_seconds = 120

  # Monitoring
  enable_cloudwatch_alarms = true

  tags = {
    Project     = "elo-fraud"
    Environment = "staging"
    ManagedBy   = "terraform"
  }
}
```

### Uso Completo (Producao)

```hcl
module "firehose" {
  source = "../../modules/firehose"

  project_name = "elo-fraud"
  environment  = "prod"
  stream_name  = "elo-fraud-transactions-firehose-prod"

  # Descricao para tags
  purpose_description = "Production Transaction Results"

  # S3 destination
  s3_bucket_arn = module.s3.data_processed_bucket_arn
  s3_prefix     = "landing_zone"

  # Buffer otimizado para producao
  buffer_size_mb          = 10   # Arquivos maiores
  buffer_interval_seconds = 300  # 5 minutos

  # Monitoring habilitado
  enable_cloudwatch_alarms = true

  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    ManagedBy   = "terraform"
    CostCenter  = "fraud-detection"
  }
}
```

### Multiplos Streams

```hcl
# Stream para transacoes
module "firehose_transactions" {
  source = "../../modules/firehose"

  project_name        = "elo-fraud"
  environment         = "staging"
  stream_name         = "elo-fraud-transactions-firehose-staging"
  purpose_description = "Transaction Results"
  s3_bucket_arn       = module.s3.data_processed_bucket_arn
  s3_prefix           = "transactions"
}

# Stream para inference logs
module "firehose_inference" {
  source = "../../modules/firehose"

  project_name        = "elo-fraud"
  environment         = "staging"
  stream_name         = "elo-fraud-inference-firehose-staging"
  purpose_description = "Inference Logs"
  s3_bucket_arn       = module.s3.data_processed_bucket_arn
  s3_prefix           = "inference_logs"
}
```

---

## Variaveis

### Obrigatorias

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `project_name` | `string` | Nome do projeto |
| `environment` | `string` | Ambiente (dev, staging, prod) |
| `stream_name` | `string` | Nome do Firehose Delivery Stream |
| `s3_bucket_arn` | `string` | ARN do bucket S3 de destino |

### Opcional

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `purpose_description` | `string` | `Transaction Results...` | Descricao para tags |

### S3 Destination

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `s3_prefix` | `string` | `landing_zone` | Prefixo no S3 |

### Buffer

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `buffer_size_mb` | `number` | `1` | Tamanho do buffer (1-128 MB) |
| `buffer_interval_seconds` | `number` | `60` | Intervalo do buffer (60-900 s) |

### Monitoring

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `enable_cloudwatch_alarms` | `bool` | `true` | Criar alarmes CloudWatch |

### Tags

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `tags` | `map(string)` | `{}` | Tags adicionais |

---

## Outputs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `delivery_stream_id` | `string` | ID do stream |
| `delivery_stream_name` | `string` | Nome do stream (para `put_record`) |
| `delivery_stream_arn` | `string` | ARN do stream |
| `firehose_role_arn` | `string` | ARN da IAM Role |
| `cloudwatch_log_group_name` | `string` | Nome do log group |
| `s3_prefix` | `string` | Prefixo S3 configurado |
| `alarm_delivery_failed_name` | `string` | Nome do alarme (se habilitado) |
| `firehose_summary` | `object` | Resumo completo da configuracao |

### Exemplo de Uso dos Outputs

```python
# No codigo Python do servico process
import boto3

firehose = boto3.client('firehose')

# Usar o nome do stream do output do Terraform
stream_name = "elo-fraud-transactions-firehose-staging"

# Enviar record
firehose.put_record(
    DeliveryStreamName=stream_name,
    Record={
        'Data': json.dumps({
            'transaction_id': 12345,
            'fraud_score': 0.85,
            'timestamp': '2024-01-15T14:30:00Z'
        }) + '\n'  # Newline para JSON Lines
    }
)
```

---

## Operacoes

### Verificar Status do Stream

```bash
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --region sa-east-1
```

### Enviar Record de Teste

```bash
aws firehose put-record \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --record '{"Data":"eyJ0ZXN0IjogdHJ1ZX0K"}' \
  --region sa-east-1
```

> Nota: Data deve ser Base64 encoded. `eyJ0ZXN0IjogdHJ1ZX0K` = `{"test": true}\n`

### Verificar Arquivos no S3

```bash
# Listar arquivos do dia atual
aws s3 ls s3://elo-fraud-data-processed-staging-888577064416/landing_zone/year=$(date +%Y)/month=$(date +%m)/day=$(date +%d)/ \
  --recursive
```

### Ver Logs de Erro

```bash
aws logs tail /aws/kinesisfirehose/elo-fraud-transactions-firehose-staging \
  --region sa-east-1 \
  --follow
```

### Verificar Metricas

```bash
# Records recebidos na ultima hora
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=elo-fraud-transactions-firehose-staging \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region sa-east-1
```

### Listar Streams

```bash
aws firehose list-delivery-streams --region sa-east-1
```

---

## Troubleshooting

### Erro: Records nao aparecem no S3

**Sintoma**: `put_record` retorna sucesso, mas arquivos nao aparecem no S3.

**Causas possiveis**:
1. Buffer ainda nao atingiu threshold
2. Erro de permissao no S3

**Solucao**:
```bash
# 1. Aguardar o buffer_interval (60s por padrao)

# 2. Verificar status do stream
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus' \
  --region sa-east-1

# 3. Verificar logs de erro
aws logs tail /aws/kinesisfirehose/elo-fraud-transactions-firehose-staging \
  --region sa-east-1 \
  --since 1h
```

---

### Erro: Access Denied ao S3

**Sintoma**: Logs mostram "Access Denied" ao tentar escrever no S3.

**Causa**: IAM Role sem permissao no bucket de destino.

**Solucao**:
```bash
# Verificar role do stream
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --query 'DeliveryStreamDescription.Destinations[0].ExtendedS3DestinationDescription.RoleARN' \
  --region sa-east-1

# Verificar policies da role
aws iam list-attached-role-policies \
  --role-name elo-fraud-transactions-firehose-staging-role
```

---

### Erro: Stream em estado CREATING por muito tempo

**Sintoma**: Stream fica em `CREATING` por mais de 5 minutos.

**Causa**: Problema com IAM role ou bucket S3.

**Solucao**:
```bash
# Verificar status detalhado
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --region sa-east-1

# Se necessario, deletar e recriar
terraform destroy -target=module.firehose
terraform apply -target=module.firehose
```

---

### Erro: DataFreshness muito alto

**Sintoma**: Metrica `DeliveryToS3.DataFreshness` muito alta (> 5 min).

**Causa**: Buffer grande ou intervalo longo.

**Solucao**: Reduzir buffer para ambiente de desenvolvimento:
```hcl
buffer_size_mb          = 1
buffer_interval_seconds = 60
```

---

### Verificar Saude do Stream

```bash
# Status do stream
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-staging \
  --query 'DeliveryStreamDescription.{Status:DeliveryStreamStatus,CreateTimestamp:CreateTimestamp}' \
  --region sa-east-1

# Metricas das ultimas 6 horas
aws cloudwatch get-metric-data \
  --metric-data-queries '[
    {
      "Id": "incoming",
      "MetricStat": {
        "Metric": {
          "Namespace": "AWS/Firehose",
          "MetricName": "IncomingRecords",
          "Dimensions": [{"Name": "DeliveryStreamName", "Value": "elo-fraud-transactions-firehose-staging"}]
        },
        "Period": 3600,
        "Stat": "Sum"
      }
    }
  ]' \
  --start-time $(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --region sa-east-1
```

---

## Custos Estimados

### Precos (sa-east-1)

| Componente | Preco |
|------------|-------|
| **Firehose Ingestion** | $0.029 / GB |
| **S3 PUT** | $0.005 / 1000 requests |
| **S3 Storage** | $0.023 / GB / mes |
| **CloudWatch Logs** | $0.50 / GB ingerido |

### Estimativa por Volume

| Volume Diario | Firehose | S3 PUT | Total/Mes |
|---------------|----------|--------|-----------|
| 1 GB/dia | ~$0.87 | ~$0.15 | ~$1.00 |
| 10 GB/dia | ~$8.70 | ~$1.50 | ~$10.00 |
| 100 GB/dia | ~$87.00 | ~$15.00 | ~$100.00 |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Compression UNCOMPRESSED** | Facilita leitura direta e debug |
| **Particionamento Hive-style** | Compativel com Athena, Glue, Spark |
| **Buffer 1MB/60s (dev)** | Feedback rapido para desenvolvimento |
| **S3 backup Disabled** | Dados primarios, nao requer backup duplicado |
| **Managed policies** | SCP bloqueia criacao de custom policies |
| **Log retention 7 dias** | Suficiente para debug, custo reduzido |

---

## Referencias

- [Amazon Kinesis Data Firehose Developer Guide](https://docs.aws.amazon.com/firehose/latest/dev/)
- [Firehose S3 Destination](https://docs.aws.amazon.com/firehose/latest/dev/create-destination.html#create-destination-s3)
- [Firehose Buffering Hints](https://docs.aws.amazon.com/firehose/latest/dev/basic-deliver.html#frequency)
- [Firehose Metrics](https://docs.aws.amazon.com/firehose/latest/dev/monitoring-with-cloudwatch-metrics.html)
