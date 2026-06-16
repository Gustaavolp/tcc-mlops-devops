# Lambda - Register Best Model

Esta Lambda consulta o MLflow, identifica o melhor modelo baseado na metrica especificada e registra no Model Registry.

## Funcionalidade

1. Busca o experimento mais recente com tag `stage=prod`
2. Identifica o melhor run baseado na metrica `f1_oot`
3. Compara com o modelo atualmente registrado
4. Registra o novo modelo se for melhor que o atual

## Variaveis de Ambiente

| Variavel | Descricao | Exemplo |
|----------|-----------|---------|
| `MODEL_NAME` | Nome do modelo no registry | `Felicidade` |
| `METRIC_TO_COMPARE` | Metrica para comparacao | `metrics.f1_oot` |
| `MLFLOW_TRACKING_URI` | URI do MLflow | `arn:aws:sagemaker:...` |
| `MLFLOW_BEST_MODEL_RUN` | Nome do artefato do modelo | `best_estimator` |
| `MLFLOW_TARGET_TAG_KEY` | Chave da tag do experimento | `stage` |
| `MLFLOW_TARGET_TAG` | Valor da tag do experimento | `prod` |

## Build

```bash
# Build da imagem
docker build -t best-model-register .

# Tag para ECR (dev)
docker tag best-model-register:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev:latest

# Tag para ECR (staging)
docker tag best-model-register:latest \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com/best-model-register-staging:latest
```

## Push para ECR

```bash
# Login no ECR (dev - us-east-1)
aws ecr get-login-password --region us-east-1 --profile elo | \
  docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-1.amazonaws.com

# Push para dev
docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev:latest

# Login no ECR (staging - sa-east-1)
aws ecr get-login-password --region sa-east-1 --profile elo | \
  docker login --username AWS --password-stdin 888577064416.dkr.ecr.sa-east-1.amazonaws.com

# Push para staging
docker push 888577064416.dkr.ecr.sa-east-1.amazonaws.com/best-model-register-staging:latest
```

## Teste Local

```bash
# Executar container localmente
docker run -p 9000:8080 \
  -e MODEL_NAME=Felicidade \
  -e METRIC_TO_COMPARE=metrics.f1_oot \
  -e MLFLOW_TRACKING_URI=<mlflow-uri> \
  -e MLFLOW_BEST_MODEL_RUN=best_estimator \
  -e MLFLOW_TARGET_TAG_KEY=stage \
  -e MLFLOW_TARGET_TAG=prod \
  best-model-register

# Invocar a Lambda
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{}'
```

## Trigger

A Lambda e acionada via S3 Notification quando objetos sao criados no bucket SageMaker (`sagemaker-{region}-{account_id}`).

## Arquitetura

```
S3 (sagemaker bucket)
    |
    v (S3 Event Notification)
Lambda (register-best-model)
    |
    v (MLflow API)
MLflow Model Registry
```

## Dependencias

- `boto3` - AWS SDK
- `python-dotenv` - Carrega variaveis de ambiente
- `mlflow==3.4.0` - MLflow client
- `sagemaker-mlflow` - Integracao SageMaker com MLflow
