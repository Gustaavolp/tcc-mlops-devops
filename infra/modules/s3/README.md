# Modulo S3 (Simple Storage Service)

## Sumario

- [Visao Geral](#visao-geral)
- [Recursos Criados](#recursos-criados)
- [Variaveis](#variaveis)
  - [Obrigatorias](#obrigatorias)
  - [Opcionais](#opcionais)
- [Outputs](#outputs)
  - [Bucket Raw](#bucket-raw)
  - [Bucket Processed](#bucket-processed)
  - [Bucket Models](#bucket-models)
  - [Bucket Logs](#bucket-logs)
  - [Bucket Resources](#bucket-resources)
  - [Bucket Reports Promotion](#bucket-reports-promotion)
  - [Bucket Reports Statistics](#bucket-reports-statistics)
  - [Agregados](#agregados)
- [Uso](#uso)
  - [Exemplo Basico](#exemplo-basico)
  - [Exemplo com Tags](#exemplo-com-tags)
- [Arquitetura](#arquitetura)
- [Operacoes](#operacoes)
- [Referencias](#referencias)

---

## Visao Geral

| Item | Descricao |
|------|-----------|
| **Proposito** | Criar buckets S3 para Data Lake (dados brutos, processados, modelos ML, logs, recursos e relatorios) |
| **Provider** | AWS S3 |
| **Tipo** | Object Storage |
| **Durabilidade** | 99.999999999% (11 noves) |
| **Disponibilidade** | 99.99% |

### Caracteristicas Principais

| Caracteristica | Descricao |
|----------------|-----------|
| **7 Buckets** | Raw, Processed, Models, Logs, Resources, Reports Promotion, Reports Statistics |
| **Nomes Customizaveis** | Nome de cada bucket definido via variavel |
| **Tags** | Tags comuns aplicadas a todos os buckets |

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_s3_bucket.raw` | Bucket | Armazena dados brutos (3DS + TE40) |
| `aws_s3_bucket.processed` | Bucket | Armazena dados processados |
| `aws_s3_bucket.models` | Bucket | Armazena artefatos de modelos ML |
| `aws_s3_bucket.logs` | Bucket | Armazena logs centralizados |
| `aws_s3_bucket.resources` | Bucket | Armazena recursos estaticos (templates, configs) |
| `aws_s3_bucket.reports_promotion` | Bucket | Armazena relatorios de promocao |
| `aws_s3_bucket.reports_statistics` | Bucket | Armazena relatorios estatisticos |

---

## Variaveis

### Obrigatorias

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `project_name` | `string` | Nome do projeto |
| `environment` | `string` | Ambiente (dev, staging, prd) |
| `raw_bucket_name` | `string` | Nome do bucket para dados raw (3DS + TE40) |
| `processed_bucket_name` | `string` | Nome do bucket para dados processados |
| `models_bucket_name` | `string` | Nome do bucket para artefatos de modelos ML |
| `logs_bucket_name` | `string` | Nome do bucket para logs centralizados |
| `resources_bucket_name` | `string` | Nome do bucket para recursos estaticos (templates, configs) |
| `reports_promotion_bucket_name` | `string` | Nome do bucket para relatorios de promocao |
| `reports_statistics_bucket_name` | `string` | Nome do bucket para relatorios estatisticos |

### Opcionais

| Variavel | Tipo | Default | Descricao |
|----------|------|---------|-----------|
| `tags` | `map(string)` | `{}` | Tags comuns aplicadas a todos os buckets |

---

## Outputs

### Bucket Raw

| Output | Tipo | Descricao |
|--------|------|-----------|
| `raw_bucket_id` | `string` | ID do bucket de dados raw |
| `raw_bucket_arn` | `string` | ARN do bucket de dados raw |
| `raw_bucket_domain_name` | `string` | Domain name do bucket raw |

### Bucket Processed

| Output | Tipo | Descricao |
|--------|------|-----------|
| `processed_bucket_id` | `string` | ID do bucket de dados processed |
| `processed_bucket_arn` | `string` | ARN do bucket de dados processed |
| `processed_bucket_domain_name` | `string` | Domain name do bucket processed |

### Bucket Models

| Output | Tipo | Descricao |
|--------|------|-----------|
| `models_bucket_id` | `string` | ID do bucket de modelos |
| `models_bucket_arn` | `string` | ARN do bucket de modelos |
| `models_bucket_domain_name` | `string` | Domain name do bucket models |

### Bucket Logs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `logs_bucket_id` | `string` | ID do bucket de logs |
| `logs_bucket_arn` | `string` | ARN do bucket de logs |
| `logs_bucket_domain_name` | `string` | Domain name do bucket logs |

### Bucket Resources

| Output | Tipo | Descricao |
|--------|------|-----------|
| `resources_bucket_id` | `string` | ID do bucket de recursos |
| `resources_bucket_arn` | `string` | ARN do bucket de recursos |
| `resources_bucket_domain_name` | `string` | Domain name do bucket resources |

### Bucket Reports Promotion

| Output | Tipo | Descricao |
|--------|------|-----------|
| `reports_promotion_bucket_id` | `string` | ID do bucket de reports promotion |
| `reports_promotion_bucket_arn` | `string` | ARN do bucket de reports promotion |
| `reports_promotion_bucket_domain_name` | `string` | Domain name do bucket reports promotion |

### Bucket Reports Statistics

| Output | Tipo | Descricao |
|--------|------|-----------|
| `reports_statistics_bucket_id` | `string` | ID do bucket de reports statistics |
| `reports_statistics_bucket_arn` | `string` | ARN do bucket de reports statistics |
| `reports_statistics_bucket_domain_name` | `string` | Domain name do bucket reports statistics |

### Agregados

| Output | Tipo | Descricao |
|--------|------|-----------|
| `all_bucket_ids` | `list(string)` | Lista de todos os IDs de buckets |
| `all_bucket_arns` | `list(string)` | Lista de todos os ARNs de buckets |
| `s3_buckets_summary` | `object` | Resumo completo de todos os buckets |

---

## Uso

### Exemplo Basico

```hcl
module "s3" {
  source = "../../modules/s3"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes dos buckets (obrigatorios)
  raw_bucket_name               = "elo-fraud-data-raw-dev-123456789012"
  processed_bucket_name         = "elo-fraud-data-processed-dev-123456789012"
  models_bucket_name            = "elo-fraud-models-dev-123456789012"
  logs_bucket_name              = "elo-fraud-logs-dev-123456789012"
  resources_bucket_name         = "elo-fraud-resources-dev-123456789012"
  reports_promotion_bucket_name = "elo-fraud-reports-promotion-dev-123456789012"
  reports_statistics_bucket_name = "elo-fraud-reports-statistics-dev-123456789012"
}
```

### Exemplo com Tags

```hcl
module "s3" {
  source = "../../modules/s3"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "prod"

  # Nomes dos buckets
  raw_bucket_name               = "elo-fraud-data-raw-prod-123456789012"
  processed_bucket_name         = "elo-fraud-data-processed-prod-123456789012"
  models_bucket_name            = "elo-fraud-models-prod-123456789012"
  logs_bucket_name              = "elo-fraud-logs-prod-123456789012"
  resources_bucket_name         = "elo-fraud-resources-prod-123456789012"
  reports_promotion_bucket_name = "elo-fraud-reports-promotion-prod-123456789012"
  reports_statistics_bucket_name = "elo-fraud-reports-statistics-prod-123456789012"

  # Tags
  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    Team        = "data-engineering"
    CostCenter  = "data-platform"
  }
}

# Usar os buckets em outros recursos
output "data_lake_buckets" {
  value = {
    raw               = module.s3.raw_bucket_id
    processed         = module.s3.processed_bucket_id
    models            = module.s3.models_bucket_id
    logs              = module.s3.logs_bucket_id
    resources         = module.s3.resources_bucket_id
    reports_promotion = module.s3.reports_promotion_bucket_id
    reports_statistics = module.s3.reports_statistics_bucket_id
  }
}
```

### Exemplo de Uso com Glue

```hcl
# Configurar Glue Job para usar buckets
resource "aws_glue_job" "etl" {
  name     = "elo-fraud-etl"
  role_arn = aws_iam_role.glue.arn

  command {
    script_location = "s3://${module.s3.resources_bucket_id}/scripts/etl.py"
  }

  default_arguments = {
    "--input_path"  = "s3://${module.s3.raw_bucket_id}/3ds/"
    "--output_path" = "s3://${module.s3.processed_bucket_id}/landing_zone/"
  }
}
```

### Exemplo de Uso com SageMaker

```hcl
# Configurar SageMaker para usar bucket de modelos
resource "aws_sagemaker_model" "fraud_detection" {
  name               = "fraud-detection-model"
  execution_role_arn = aws_iam_role.sagemaker.arn

  primary_container {
    image          = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/fraud-model:latest"
    model_data_url = "s3://${module.s3.models_bucket_id}/fraud-detection/latest/model.tar.gz"
  }
}
```

---

## Arquitetura

### Data Lake Architecture

```
+-----------------------------------------------------------------------------+
|                           DATA LAKE ARCHITECTURE                            |
+-----------------------------------------------------------------------------+
|                                                                             |
|   INGESTAO                                                                  |
|   ========                                                                  |
|                                                                             |
|   Elo Cartoes ─────────────────────────────────┐                           |
|       │                                         │                           |
|       ├── 3DS (Three-Domain Secure)            │                           |
|       └── TE40 (Transacoes)                    │                           |
|                                                 ▼                           |
|                                    +------------------------+               |
|                                    |    S3 BUCKET RAW       |               |
|                                    |  (dados brutos)        |               |
|                                    +------------------------+               |
|                                                 │                           |
|                                                 │ ETL (Glue/Lambda)         |
|                                                 ▼                           |
|   PROCESSAMENTO                   +------------------------+               |
|   =============                   |  S3 BUCKET PROCESSED   |               |
|                                    |  (camadas de dados)    |               |
|                                    +------------------------+               |
|                                                 │                           |
|                                                 ▼                           |
|   ML/AI                           +------------------------+               |
|   =====                           |   S3 BUCKET MODELS     |               |
|                                    |  (artefatos ML)        |               |
|   SageMaker ◄─────────────────────|                        |               |
|                                    +------------------------+               |
|                                                                             |
|   OBSERVABILIDADE                 +------------------------+               |
|   ===============                 |   S3 BUCKET LOGS       |               |
|                                    |  (logs centralizados)  |               |
|                                    +------------------------+               |
|                                                                             |
|   RECURSOS                        +------------------------+               |
|   ========                        |  S3 BUCKET RESOURCES   |               |
|                                    |  (templates, configs)  |               |
|                                    +------------------------+               |
|                                                                             |
|   RELATORIOS                      +------------------------+               |
|   ==========                      | S3 REPORTS PROMOTION   |               |
|                                    +------------------------+               |
|                                    +------------------------+               |
|                                    | S3 REPORTS STATISTICS  |               |
|                                    +------------------------+               |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Operacoes

### Listar Buckets

```bash
# Listar todos os buckets do projeto
aws s3 ls | grep elo-fraud

# Ver conteudo de um bucket
aws s3 ls s3://elo-fraud-data-raw-dev-123456789012/ --recursive

# Ver tamanho total de um bucket
aws s3 ls s3://elo-fraud-data-raw-dev-123456789012/ --recursive --summarize
```

### Upload/Download

```bash
# Upload de arquivo
aws s3 cp local-file.parquet s3://elo-fraud-data-raw-dev-123456789012/3ds/

# Upload de diretorio
aws s3 sync ./data/ s3://elo-fraud-data-raw-dev-123456789012/3ds/ --exclude "*.tmp"

# Download de arquivo
aws s3 cp s3://elo-fraud-models-dev-123456789012/fraud-detection/latest/model.tar.gz ./
```

### Verificar Criptografia

```bash
# Ver configuracao de criptografia
aws s3api get-bucket-encryption \
  --bucket elo-fraud-data-raw-dev-123456789012

# Ver criptografia de um objeto especifico
aws s3api head-object \
  --bucket elo-fraud-data-raw-dev-123456789012 \
  --key 3ds/data.parquet \
  --query "ServerSideEncryption"
```

---

## Referencias

### AWS Documentation

- [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/)
- [S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/)
- [S3 Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingEncryption.html)

### Terraform Documentation

- [aws_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket)
