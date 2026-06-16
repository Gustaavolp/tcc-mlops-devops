# Modulo MLflow

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Tamanhos de Servidor](#tamanhos-de-servidor)
- [S3 Artifacts](#s3-artifacts)
- [Integracao com SageMaker](#integracao-com-sagemaker)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona um **MLflow Tracking Server** gerenciado pela AWS SageMaker para rastreamento de experimentos de Machine Learning, versionamento de modelos e armazenamento de artifacts.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Experiment Tracking** | Registra metricas, parametros e artifacts de experimentos ML |
| **Model Registry** | Versionamento centralizado de modelos de ML |
| **Artifact Storage** | Armazenamento de artifacts em S3 (modelos, datasets, plots) |
| **Collaboration** | Interface web para visualizacao e comparacao de experimentos |

### Por que MLflow Managed?

| Beneficio | Descricao |
|-----------|-----------|
| **Serverless** | AWS gerencia infraestrutura, upgrades e patches |
| **Integracao Nativa** | Funciona com SageMaker Studio, Notebooks e Training Jobs |
| **Escalabilidade** | Escala automaticamente conforme demanda |
| **Seguranca** | IAM integrado, criptografia, VPC opcional |
| **Model Registry** | Registro automatico de modelos no SageMaker Model Registry |

### Caracteristicas Principais

| Caracteristica | Valor Padrao | Descricao |
|----------------|--------------|-----------|
| **MLflow Version** | 3.0 | Versao do MLflow |
| **Server Size** | Small | Tamanho da instancia |
| **Auto Model Registration** | true | Registro automatico de modelos |
| **Maintenance Window** | Sun:03:00 | Janela de manutencao semanal |
| **Log Retention** | 7 dias | Retencao de logs no CloudWatch |

---

## Arquitetura

```
                              MLflow Tracking Server (SageMaker Managed)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              AWS SageMaker                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                          │  │
│   │                    MLflow Tracking Server                                │  │
│   │                                                                          │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │  │
│   │   │                                                                  │   │  │
│   │   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │   │  │
│   │   │   │  Tracking   │  │   Model     │  │  Artifact   │            │   │  │
│   │   │   │   Server    │  │  Registry   │  │   Store     │            │   │  │
│   │   │   │             │  │             │  │             │            │   │  │
│   │   │   │ Experiments │  │  Versions   │  │    S3       │            │   │  │
│   │   │   │ Runs        │  │  Stages     │  │  Bucket     │            │   │  │
│   │   │   │ Metrics     │  │  Aliases    │  │             │            │   │  │
│   │   │   └─────────────┘  └─────────────┘  └─────────────┘            │   │  │
│   │   │                                                                  │   │  │
│   │   │   URL: https://{server}.{region}.sagemaker.aws/                 │   │  │
│   │   │                                                                  │   │  │
│   │   └─────────────────────────────────────────────────────────────────┘   │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                        │
│              ┌─────────────────────────┼─────────────────────────┐             │
│              │                         │                         │             │
│              ▼                         ▼                         ▼             │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐       │
│   │   IAM Role      │      │  S3 Bucket      │      │  CloudWatch     │       │
│   │                 │      │  (Artifacts)    │      │  Logs           │       │
│   │ - SageMaker     │      │                 │      │                 │       │
│   │ - S3 Full       │      │ - Versioning    │      │ /aws/sagemaker  │       │
│   │ - CloudWatch    │      │ - Encryption    │      │ /mlflow/...     │       │
│   │ - Firehose      │      │ - Lifecycle     │      │                 │       │
│   │ - Bedrock       │      │ - Tiering       │      │                 │       │
│   └─────────────────┘      └─────────────────┘      └─────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MLflow Data Flow                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐             │
│   │  SageMaker    │      │   Notebooks   │      │  Training     │             │
│   │    Studio     │      │   (Jupyter)   │      │    Jobs       │             │
│   └───────┬───────┘      └───────┬───────┘      └───────┬───────┘             │
│           │                      │                      │                      │
│           └──────────────────────┼──────────────────────┘                      │
│                                  │                                              │
│                                  │  mlflow.set_tracking_uri()                  │
│                                  │  mlflow.log_param()                         │
│                                  │  mlflow.log_metric()                        │
│                                  │  mlflow.log_artifact()                      │
│                                  ▼                                              │
│                       ┌───────────────────┐                                    │
│                       │  MLflow Tracking  │                                    │
│                       │     Server        │                                    │
│                       └─────────┬─────────┘                                    │
│                                 │                                               │
│              ┌──────────────────┼──────────────────┐                           │
│              │                  │                  │                           │
│              ▼                  ▼                  ▼                           │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│   │    Metadata     │  │    Artifacts    │  │     Models      │              │
│   │   (Backend)     │  │      (S3)       │  │   (Registry)    │              │
│   │                 │  │                 │  │                 │              │
│   │ - Experiments   │  │ - model.pkl     │  │ - Versioning    │              │
│   │ - Runs          │  │ - plots.png     │  │ - Staging       │              │
│   │ - Params        │  │ - data.csv      │  │ - Production    │              │
│   │ - Metrics       │  │ - requirements  │  │ - Archived      │              │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

### AWS Resources

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| **MLflow Tracking Server** | `aws_sagemaker_mlflow_tracking_server` | Servidor MLflow gerenciado |
| **S3 Bucket** | `aws_s3_bucket` | Armazenamento de artifacts |
| **S3 Versioning** | `aws_s3_bucket_versioning` | Versionamento de artifacts |
| **S3 Encryption** | `aws_s3_bucket_server_side_encryption_configuration` | Criptografia SSE-S3 ou KMS |
| **S3 Lifecycle** | `aws_s3_bucket_lifecycle_configuration` | Regras de expiracao e tiering |
| **IAM Role** | `aws_iam_role` | Role para execucao do MLflow |
| **IAM Policies** | `aws_iam_role_policy_attachment` | Managed policies anexadas |
| **CloudWatch Log Group** | `aws_cloudwatch_log_group` | Logs do servidor |

### Diagrama de Recursos

```
aws_sagemaker_mlflow_tracking_server.main
    │
    ├── Depends on: aws_iam_role.execution
    │       │
    │       ├── aws_iam_role_policy_attachment.sagemaker_full_access
    │       ├── aws_iam_role_policy_attachment.s3_full_access
    │       ├── aws_iam_role_policy_attachment.cloudwatch_logs_full_access
    │       ├── aws_iam_role_policy_attachment.firehose_full_access
    │       └── aws_iam_role_policy_attachment.bedrock_full_access
    │
    ├── Depends on: aws_s3_bucket.artifacts
    │       │
    │       ├── aws_s3_bucket_versioning.artifacts
    │       ├── aws_s3_bucket_server_side_encryption_configuration.artifacts
    │       └── aws_s3_bucket_lifecycle_configuration.artifacts
    │
    └── Depends on: aws_cloudwatch_log_group.mlflow
```

### IAM Policies Anexadas

| Policy | Proposito |
|--------|-----------|
| `AmazonSageMakerFullAccess` | Operacoes SageMaker e MLflow |
| `AmazonS3FullAccess` | Leitura/escrita de artifacts |
| `CloudWatchLogsFullAccess` | Logs do servidor |
| `AmazonKinesisFirehoseFullAccess` | Streaming de dados |
| `AmazonBedrockFullAccess` | Integracao com modelos Bedrock |

---

## Tamanhos de Servidor

O MLflow Tracking Server oferece tres tamanhos de instancia.

### Opcoes Disponiveis

| Tamanho | Uso Recomendado | Usuarios Simultaneos | Experimentos |
|---------|-----------------|----------------------|--------------|
| **Small** | Desenvolvimento, POCs | Ate 10 | Ate 100 |
| **Medium** | Staging, times pequenos | Ate 50 | Ate 500 |
| **Large** | Producao, times grandes | Ate 200+ | Milhares |

### Especificacoes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Server Size Comparison                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Small                     Medium                    Large                     │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐       │
│   │                 │      │                 │      │                 │       │
│   │   Dev / Test    │      │    Staging      │      │   Production    │       │
│   │                 │      │                 │      │                 │       │
│   │   - Baixo custo │      │   - Balanceado  │      │   - Alta carga  │       │
│   │   - POCs        │      │   - Teams       │      │   - Enterprise  │       │
│   │   - Individual  │      │   - Moderado    │      │   - Multi-team  │       │
│   │                 │      │                 │      │                 │       │
│   └─────────────────┘      └─────────────────┘      └─────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Recomendacao por Ambiente

| Ambiente | Tamanho | Justificativa |
|----------|---------|---------------|
| **DEV** | Small | Desenvolvimento individual, baixo custo |
| **STAGING** | Small/Medium | Testes de integracao, uso moderado |
| **PROD** | Medium/Large | Times completos, alta disponibilidade |

---

## S3 Artifacts

O bucket S3 armazena artifacts dos experimentos MLflow.

### Estrutura de Armazenamento

```
s3://{project}-mlflow-artifacts-{env}-{account_id}/
├── experiments/
│   └── {experiment_id}/
│       └── {run_id}/
│           └── artifacts/
│               ├── model/
│               │   ├── model.pkl
│               │   ├── requirements.txt
│               │   └── MLmodel
│               ├── plots/
│               │   └── confusion_matrix.png
│               └── data/
│                   └── validation_results.csv
└── models/
    └── {model_name}/
        └── {version}/
            └── artifacts/
```

### Features do Bucket

| Feature | Configuracao | Descricao |
|---------|--------------|-----------|
| **Versioning** | Enabled | Versionamento de objetos |
| **Encryption** | AES256 ou KMS | Criptografia em repouso |
| **Lifecycle (30 dias)** | INTELLIGENT_TIERING | Reducao automatica de custos |
| **Lifecycle (expiracao)** | Configuravel | Expiracao de artifacts antigos |
| **Noncurrent Versions** | 30 dias | Expiracao de versoes antigas |

### Lifecycle Rules

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          S3 Lifecycle Rules                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Dia 0              Dia 30                    Dia N (configuravel)            │
│     │                  │                              │                         │
│     ▼                  ▼                              ▼                         │
│   ┌────────┐      ┌────────────────────┐      ┌────────────┐                  │
│   │STANDARD│─────▶│INTELLIGENT_TIERING │─────▶│  EXPIRED   │                  │
│   └────────┘      └────────────────────┘      └────────────┘                  │
│                                                                                 │
│   - Upload inicial    - Tiering automatico      - Remocao automatica          │
│   - Acesso frequente  - Frequent/Infrequent     - artifact_retention_days     │
│                       - Archive Access          - (0 = nunca expira)          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Integracao com SageMaker

O MLflow Tracking Server integra nativamente com servicos SageMaker.

### Pontos de Integracao

| Servico | Integracao | Descricao |
|---------|------------|-----------|
| **SageMaker Studio** | Nativa | UI integrada, notebooks |
| **Training Jobs** | SDK | Log automatico de metricas |
| **Processing Jobs** | SDK | Processamento de dados |
| **Model Registry** | Automatica | Registro de modelos |
| **Endpoints** | Deployment | Deploy de modelos versionados |

### Exemplo de Uso em Python

```python
import mlflow
from mlflow.tracking import MlflowClient

# Configurar tracking URI (formato AWS)
mlflow.set_tracking_uri("aws://sagemaker/elo-fraud-mlflow-staging")

# Criar ou usar experimento existente
mlflow.set_experiment("fraud-detection-xgboost")

# Treinar e logar metricas
with mlflow.start_run(run_name="training-v1"):
    # Parametros
    mlflow.log_param("learning_rate", 0.1)
    mlflow.log_param("max_depth", 6)
    mlflow.log_param("n_estimators", 100)

    # Treinar modelo...
    model = train_model(X_train, y_train)

    # Metricas
    mlflow.log_metric("auc", 0.95)
    mlflow.log_metric("precision", 0.87)
    mlflow.log_metric("recall", 0.82)

    # Artifacts
    mlflow.log_artifact("confusion_matrix.png")

    # Modelo
    mlflow.sklearn.log_model(model, "model")

# Registrar modelo no Model Registry
mlflow.register_model(
    f"runs:/{run_id}/model",
    "fraud-detection-model"
)
```

---

## Uso

### Uso Basico

```hcl
module "mlflow" {
  source = "../../modules/mlflow"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "dev"

  # Resource Names (obrigatorios)
  tracking_server_name = "elo-fraud-mlflow-dev"
  artifact_bucket_name = "elo-fraud-mlflow-artifacts-dev-${data.aws_caller_identity.current.account_id}"
  execution_role_name  = "elo-fraud-mlflow-dev-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/elo-fraud-mlflow-dev"
}
```

### Uso com Bucket Existente

```hcl
module "mlflow" {
  source = "../../modules/mlflow"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "staging"

  # Resource Names (obrigatorios)
  tracking_server_name = "elo-fraud-mlflow-staging"
  artifact_bucket_name = "not-used"  # Ignorado quando create_artifact_bucket = false
  execution_role_name  = "elo-fraud-mlflow-staging-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/elo-fraud-mlflow-staging"

  # Usar bucket S3 existente
  create_artifact_bucket = false
  artifact_store_uri     = "s3://meu-bucket-existente"
}
```

### Uso Completo

```hcl
module "mlflow" {
  source = "../../modules/mlflow"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "prod"

  # Resource Names (obrigatorios)
  tracking_server_name = "elo-fraud-mlflow-prod"
  artifact_bucket_name = "elo-fraud-mlflow-artifacts-prod-${data.aws_caller_identity.current.account_id}"
  execution_role_name  = "elo-fraud-mlflow-prod-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/elo-fraud-mlflow-prod"

  # MLflow Configuration
  tracking_server_size            = "Medium"
  mlflow_version                  = "3.0"
  automatic_model_registration    = true
  weekly_maintenance_window_start = "Sun:03:00"

  # S3 Artifacts
  create_artifact_bucket  = true
  lifecycle_rules_enabled = true
  artifact_retention_days = 365  # 1 ano

  # Security
  kms_key_id = module.kms.key_arn

  # Logs
  log_retention_days = 30

  # Tags
  tags = {
    Team        = "data-science"
    Project     = "elo-fraud"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}
```

### Uso por Ambiente

```hcl
locals {
  account_id = data.aws_caller_identity.current.account_id
}

# DEV - Baixo custo
module "mlflow_dev" {
  source = "../../modules/mlflow"

  project_name         = "elo-fraud"
  environment          = "dev"
  tracking_server_name = "elo-fraud-mlflow-dev"
  artifact_bucket_name = "elo-fraud-mlflow-artifacts-dev-${local.account_id}"
  execution_role_name  = "elo-fraud-mlflow-dev-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/elo-fraud-mlflow-dev"
  tracking_server_size = "Small"
  log_retention_days   = 7
}

# STAGING - Balanceado
module "mlflow_staging" {
  source = "../../modules/mlflow"

  project_name         = "elo-fraud"
  environment          = "staging"
  tracking_server_name = "elo-fraud-mlflow-staging"
  artifact_bucket_name = "elo-fraud-mlflow-artifacts-staging-${local.account_id}"
  execution_role_name  = "elo-fraud-mlflow-staging-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/elo-fraud-mlflow-staging"
  tracking_server_size = "Small"
  log_retention_days   = 14
}

# PROD - Alta disponibilidade
module "mlflow_prod" {
  source = "../../modules/mlflow"

  project_name            = "elo-fraud"
  environment             = "prod"
  tracking_server_name    = "elo-fraud-mlflow-prod"
  artifact_bucket_name    = "elo-fraud-mlflow-artifacts-prod-${local.account_id}"
  execution_role_name     = "elo-fraud-mlflow-prod-execution-role"
  log_group_name          = "/aws/sagemaker/mlflow/elo-fraud-mlflow-prod"
  tracking_server_size    = "Medium"
  artifact_retention_days = 730  # 2 anos
  log_retention_days      = 90
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `project_name` | string | Sim | - | Nome do projeto |
| `environment` | string | Sim | - | Ambiente (dev, staging, prod) |
| `tags` | map(string) | Nao | `{}` | Tags comuns para todos os recursos |

### Resource Names (Obrigatorios)

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tracking_server_name` | string | Sim | - | Nome do MLflow Tracking Server |
| `artifact_bucket_name` | string | Sim | - | Nome do S3 bucket para artifacts (globalmente unico) |
| `execution_role_name` | string | Sim | - | Nome da IAM Role para execucao do MLflow |
| `log_group_name` | string | Sim | - | Nome do CloudWatch Log Group |

### MLflow Configuration

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tracking_server_size` | string | Nao | `Small` | Tamanho (Small, Medium, Large) |
| `mlflow_version` | string | Nao | `3.0` | Versao do MLflow |
| `automatic_model_registration` | bool | Nao | `true` | Registro automatico de modelos |
| `weekly_maintenance_window_start` | string | Nao | `Sun:03:00` | Janela de manutencao (ddd:hh:mm) |

### S3 Artifacts

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `create_artifact_bucket` | bool | Nao | `true` | Criar bucket ou usar existente |
| `artifact_store_uri` | string | Condicional | `null` | URI S3 (se create_artifact_bucket=false) |
| `lifecycle_rules_enabled` | bool | Nao | `true` | Habilitar lifecycle rules |
| `artifact_retention_days` | number | Nao | `0` | Dias para reter (0=nunca expira) |

### Security

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `kms_key_id` | string | Nao | `null` | ARN da KMS key (null=AWS managed) |

### CloudWatch Logs

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `log_retention_days` | number | Nao | `7` | Dias de retencao de logs |

### Tags

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tags` | map(string) | Nao | `{}` | Tags adicionais |

---

## Outputs

### Tracking Server

| Output | Tipo | Descricao |
|--------|------|-----------|
| `tracking_server_name` | string | Nome do servidor MLflow |
| `tracking_server_arn` | string | ARN do servidor |
| `tracking_server_url` | string | URL da UI web |
| `mlflow_tracking_uri` | string | URI para clientes Python |
| `mlflow_version` | string | Versao do MLflow |

### IAM

| Output | Tipo | Descricao |
|--------|------|-----------|
| `execution_role_arn` | string | ARN da IAM Role |
| `execution_role_name` | string | Nome da IAM Role |

### S3 Artifacts

| Output | Tipo | Descricao |
|--------|------|-----------|
| `artifact_bucket_name` | string | Nome do bucket (ou null) |
| `artifact_bucket_arn` | string | ARN do bucket (ou null) |
| `artifact_store_uri` | string | URI S3 do artifact store |

### CloudWatch

| Output | Tipo | Descricao |
|--------|------|-----------|
| `log_group_name` | string | Nome do Log Group |
| `log_group_arn` | string | ARN do Log Group |

### Auxiliares

| Output | Tipo | Descricao |
|--------|------|-----------|
| `mlflow_connection_info` | object | Objeto com todas as informacoes |
| `usage_instructions` | string | Instrucoes de uso detalhadas |

### Exemplo de Uso dos Outputs

```hcl
# Usar em SageMaker Studio Domain
resource "aws_sagemaker_domain" "main" {
  domain_name = "elo-fraud-studio"
  # ...

  default_user_settings {
    execution_role = module.mlflow.execution_role_arn
  }
}

# Output para notebooks
output "mlflow_config" {
  value = {
    tracking_uri = module.mlflow.mlflow_tracking_uri
    ui_url       = module.mlflow.tracking_server_url
    artifacts    = module.mlflow.artifact_store_uri
  }
}

# Configurar em variaveis de ambiente
resource "kubernetes_config_map" "mlflow" {
  metadata {
    name = "mlflow-config"
  }

  data = {
    MLFLOW_TRACKING_URI = module.mlflow.mlflow_tracking_uri
  }
}
```

---

## Operacoes

### Verificar Status do Servidor

```bash
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --region sa-east-1

# Status esperado: "Created" → "Creating" → "InService"
```

### Listar Servidores

```bash
aws sagemaker list-mlflow-tracking-servers \
  --region sa-east-1
```

### Acessar UI Web

```bash
# Obter URL do servidor
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --query 'TrackingServerUrl' \
  --output text \
  --region sa-east-1

# Ou via AWS Console:
# SageMaker → MLflow → Selecionar servidor → "Open MLflow UI"
```

### Configurar Python Client

```python
import mlflow

# Metodo 1: Tracking URI formato AWS
mlflow.set_tracking_uri("aws://sagemaker/elo-fraud-mlflow-staging")

# Metodo 2: ARN direto
mlflow.set_tracking_uri("arn:aws:sagemaker:sa-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-staging")

# Verificar conexao
print(mlflow.get_tracking_uri())
client = mlflow.tracking.MlflowClient()
print(client.search_experiments())
```

### Ver Logs

```bash
# Logs do servidor
aws logs tail /aws/sagemaker/mlflow/elo-fraud-mlflow-staging \
  --region sa-east-1 \
  --follow

# Logs das ultimas 2 horas
aws logs filter-log-events \
  --log-group-name /aws/sagemaker/mlflow/elo-fraud-mlflow-staging \
  --start-time $(date -d '2 hours ago' +%s)000 \
  --region sa-east-1
```

### Verificar Artifacts no S3

```bash
# Listar buckets
aws s3 ls | grep mlflow

# Listar artifacts
aws s3 ls s3://elo-fraud-mlflow-artifacts-staging-888577064416/ --recursive

# Ver tamanho total
aws s3 ls s3://elo-fraud-mlflow-artifacts-staging-888577064416/ --recursive --summarize
```

### Iniciar/Parar Servidor

```bash
# Parar servidor (economia de custos em dev)
aws sagemaker stop-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev \
  --region sa-east-1

# Iniciar servidor
aws sagemaker start-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev \
  --region sa-east-1
```

---

## Troubleshooting

### Erro: Servidor em Creating por muito tempo

**Sintoma**: Status permanece em "Creating" por mais de 15 minutos.

**Causa**: Problema com IAM Role ou configuracao.

**Solucao**:
```bash
# Verificar eventos do servidor
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --region sa-east-1

# Verificar logs
aws logs tail /aws/sagemaker/mlflow/elo-fraud-mlflow-staging \
  --region sa-east-1

# Se necessario, deletar e recriar
terraform destroy -target=module.mlflow
terraform apply -target=module.mlflow
```

---

### Erro: Access Denied ao logar metricas

**Sintoma**:
```
AccessDeniedException: User is not authorized to perform: sagemaker-mlflow:LogMetric
```

**Causa**: IAM Role sem permissoes MLflow.

**Solucao**: Verificar se a role correta esta sendo usada:
```python
# No notebook/script, usar a execution role do MLflow
import boto3
sts = boto3.client('sts')
print(sts.get_caller_identity())

# Deve mostrar a role: elo-fraud-mlflow-staging-execution-role
```

---

### Erro: Artifacts nao aparecem no S3

**Sintoma**: `mlflow.log_artifact()` executa sem erro, mas arquivo nao aparece no S3.

**Causa**: Bucket incorreto ou permissoes S3.

**Solucao**:
```bash
# Verificar URI configurado no servidor
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --query 'ArtifactStoreUri' \
  --output text \
  --region sa-east-1

# Verificar se bucket existe
aws s3 ls s3://elo-fraud-mlflow-artifacts-staging-888577064416/
```

---

### Erro: Connection timeout ao acessar UI

**Sintoma**: Browser nao consegue acessar a URL do MLflow UI.

**Causa**: VPC configuration ou IAM permissions.

**Solucao**:
```bash
# Verificar status do servidor
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --query 'TrackingServerStatus' \
  --output text \
  --region sa-east-1

# Deve retornar: InService

# Se retornar Stopped, iniciar o servidor
aws sagemaker start-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --region sa-east-1
```

---

### Erro: Model Registry nao registra automaticamente

**Sintoma**: Modelos logados nao aparecem no Model Registry.

**Causa**: `automatic_model_registration = false` ou modelo nao logado corretamente.

**Solucao**:
```python
# Verificar configuracao
import mlflow
print(mlflow.get_tracking_uri())

# Logar modelo corretamente (isso dispara registro automatico)
with mlflow.start_run():
    mlflow.sklearn.log_model(model, "model", registered_model_name="meu-modelo")
```

---

### Verificar Saude do Sistema

```bash
# Status completo
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --region sa-east-1

# IAM Role
aws iam get-role \
  --role-name elo-fraud-mlflow-staging-execution-role

# Policies anexadas
aws iam list-attached-role-policies \
  --role-name elo-fraud-mlflow-staging-execution-role

# S3 Bucket
aws s3api head-bucket \
  --bucket elo-fraud-mlflow-artifacts-staging-888577064416
```

---

## Custos Estimados

### Precos (sa-east-1)

| Componente | Preco |
|------------|-------|
| **MLflow Small** | ~$100/mes (estimado) |
| **MLflow Medium** | ~$200/mes (estimado) |
| **MLflow Large** | ~$400/mes (estimado) |
| **S3 Storage** | $0.023/GB/mes |
| **S3 Requests** | $0.005/1000 PUT |
| **CloudWatch Logs** | $0.50/GB ingerido |

### Estimativa por Ambiente

| Ambiente | Server | Artifacts (S3) | Total Estimado |
|----------|--------|----------------|----------------|
| **DEV** | Small (~$100) | ~5 GB (~$0.12) | ~$100/mes |
| **STAGING** | Small (~$100) | ~20 GB (~$0.50) | ~$101/mes |
| **PROD** | Medium (~$200) | ~100 GB (~$2.30) | ~$203/mes |

### Dica de Economia

```bash
# Parar servidor em ambientes de dev quando nao estiver em uso
aws sagemaker stop-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev \
  --region sa-east-1

# Servidor parado = sem cobranca de compute (apenas S3)
```

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **SageMaker Managed** | Sem gerenciamento de infraestrutura, upgrades automaticos |
| **Managed Policies** | SCP bloqueia criacao de custom policies |
| **S3 Versioning** | Protecao contra delecao acidental de artifacts |
| **Intelligent Tiering** | Reducao automatica de custos para artifacts antigos |
| **Tags ignoradas na role** | SCP bloqueia `iam:TagRole` |
| **Bedrock policy anexada** | Permite uso de modelos Bedrock em notebooks |

---

## Referencias

- [AWS MLflow Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html)
- [MLflow Official Docs](https://mlflow.org/docs/latest/index.html)
- [Terraform aws_sagemaker_mlflow_tracking_server](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_mlflow_tracking_server)
- [MLflow Python API](https://mlflow.org/docs/latest/python_api/index.html)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
