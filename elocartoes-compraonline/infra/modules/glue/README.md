# Glue Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Migracao de Estado](#migracao-de-estado)
- [Integracao com Athena](#integracao-com-athena)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona a infraestrutura completa do **AWS Glue ETL**, incluindo:

- S3 Bucket para assets (scripts, logs, temp files)
- IAM Role com permissoes necessarias
- Upload automatico de scripts Python para S3
- Glue Jobs (ETL) configuraveis
- Glue Triggers (SCHEDULED e CONDITIONAL)
- Glue Catalog Database (opcional)

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **ETL Pipeline** | Jobs para processamento de dados (merge, enrich) |
| **S3 Assets** | Armazenamento de scripts, logs e arquivos temporarios |
| **Scheduling** | Triggers agendados (cron) e condicionais |
| **Data Catalog** | Repositorio central de metadados das tabelas |
| **IAM Role** | Permissoes para Glue Jobs e Crawlers |

---

## Arquitetura

```
                              AWS Glue ETL Pipeline
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        S3 Assets Bucket                                  │  │
│   │                  aws-glue-assets-{account}-{region}                     │  │
│   │                                                                          │  │
│   │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│   │   │    scripts/     │  │ sparkHistoryLogs│  │   temporary/    │        │  │
│   │   │                 │  │                 │  │                 │        │  │
│   │   │ job_training.py │  │ Spark UI logs   │  │ Temp files      │        │  │
│   │   │ job_enrich.py   │  │                 │  │                 │        │  │
│   │   └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                        │
│              ┌─────────────────────────┴─────────────────────────┐             │
│              │                                                   │             │
│              ▼                                                   ▼             │
│   ┌─────────────────────────┐               ┌─────────────────────────┐       │
│   │      Glue Job 1         │               │      Glue Job 2         │       │
│   │   job_training_test_1   │──SUCCEEDED───▶│   job_backfill_enrich   │       │
│   │                         │               │                         │       │
│   │  Landing → Transformed  │               │  Feature Engineering    │       │
│   │  (Delta Lake MERGE)     │               │  (User, Merchant, Time) │       │
│   └─────────────────────────┘               └─────────────────────────┘       │
│              ▲                                                                 │
│              │                                                                 │
│   ┌─────────────────────────┐                                                 │
│   │   Scheduled Trigger     │                                                 │
│   │   cron(0 8 ? * SUN *)   │                                                 │
│   │   Domingo 08:00 UTC     │                                                 │
│   └─────────────────────────┘                                                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline ETL

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   Trigger SCHEDULED (Domingo 08:00 UTC)                                        │
│        │                                                                        │
│        ▼                                                                        │
│   Job 1: job_training_test_1                                                    │
│        │  - Lê da landing_zone                                                  │
│        │  - MERGE incremental para transformed_zone                            │
│        │  - Delta Lake format                                                   │
│        │                                                                        │
│        ▼                                                                        │
│   Trigger CONDITIONAL (SUCCEEDED)                                               │
│        │                                                                        │
│        ▼                                                                        │
│   Job 2: job_backfill_enrich                                                    │
│        │  - Feature engineering                                                 │
│        │  - User features (historico, frequencia)                               │
│        │  - Merchant features (fraudes historicas)                              │
│        │  - Temporal features (dia, hora)                                       │
│        │                                                                        │
│        ▼                                                                        │
│   Dados prontos para ML Training                                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_iam_role.glue` | IAM Role | Role de execucao para Glue Jobs |
| `aws_iam_role_policy_attachment.glue_s3` | Policy | AmazonS3FullAccess |
| `aws_iam_role_policy_attachment.glue_console` | Policy | AWSGlueConsoleFullAccess |
| `aws_iam_role_policy_attachment.glue_logs` | Policy | CloudWatchLogsFullAccess |
| `aws_s3_bucket.glue_assets` | S3 Bucket | Bucket para assets (opcional) |
| `aws_s3_bucket_versioning.glue_assets` | Versioning | Versionamento habilitado |
| `aws_s3_bucket_server_side_encryption_configuration.glue_assets` | Encryption | SSE-S3 (AES256) |
| `aws_s3_bucket_public_access_block.glue_assets` | Public Block | Bloqueia acesso publico |
| `aws_s3_object.scripts` | S3 Objects | Upload de scripts Python |
| `aws_glue_job.jobs` | Glue Jobs | Jobs ETL configuraveis |
| `aws_glue_trigger.scheduled` | Triggers | Triggers SCHEDULED (cron) |
| `aws_glue_trigger.conditional` | Triggers | Triggers CONDITIONAL |
| `aws_glue_catalog_database.main` | Database | Glue Catalog Database (opcional) |

---

## Uso

### Uso Completo (Pipeline ETL)

```hcl
locals {
  glue_assets_bucket_name = "aws-glue-assets-${var.aws_account_id}-${var.aws_region}"
  glue_scripts_local_path = "${path.module}/../../../../glue"
  data_processed_bucket   = "elo-fraud-data-processed-${var.environment}-${var.aws_account_id}"
}

module "glue" {
  source = "../../../modules/glue"

  project_name = var.project_name
  environment  = var.environment

  # IAM Role
  role_name = "${var.project_name}-glue-role-${var.environment}"

  # Glue Database (ja existe via Athena)
  create_database = false
  database_name   = module.athena.database_name

  # S3 Assets Bucket
  create_assets_bucket = true
  assets_bucket_name   = local.glue_assets_bucket_name

  # Scripts ETL
  scripts = [
    {
      name       = "training"
      s3_key     = "scripts/job_training_test_1.py"
      local_path = "${local.glue_scripts_local_path}/job_training_test_1.py"
    },
    {
      name       = "enrich"
      s3_key     = "scripts/job_backfill_enrich.py"
      local_path = "${local.glue_scripts_local_path}/job_backfill_enrich.py"
    }
  ]

  # Glue Jobs
  jobs = [
    {
      name                = "job_training_test_1"
      description         = "Merge dados da landing_zone para transformed_zone"
      script_name         = "training"
      glue_version        = "5.0"
      worker_type         = "G.1X"
      number_of_workers   = 10
      timeout             = 480
      max_retries         = 0
      max_concurrent_runs = 1
      default_arguments = {
        "--enable-metrics"               = "true"
        "--spark-event-logs-path"        = "s3://${local.glue_assets_bucket_name}/sparkHistoryLogs/"
        "--enable-job-insights"          = "true"
        "--enable-observability-metrics" = "true"
        "--enable-glue-datacatalog"      = "true"
        "--job-bookmark-option"          = "job-bookmark-disable"
        "--job-language"                 = "python"
        "--TempDir"                      = "s3://${local.glue_assets_bucket_name}/temporary/"
        "--datalake-formats"             = "delta"
        "--INPUT_PATH"                   = "s3://${local.data_processed_bucket}/inference_logs/"
        "--OUTPUT_PATH"                  = "s3://${local.data_processed_bucket}/transformed_zone/"
      }
    },
    {
      name                = "job_backfill_enrich"
      description         = "Feature engineering"
      script_name         = "enrich"
      glue_version        = "5.0"
      worker_type         = "G.1X"
      number_of_workers   = 10
      timeout             = 480
      max_retries         = 0
      max_concurrent_runs = 1
      default_arguments = {
        "--enable-metrics"               = "true"
        "--enable-spark-ui"              = "true"
        "--spark-event-logs-path"        = "s3://${local.glue_assets_bucket_name}/sparkHistoryLogs/"
        "--enable-job-insights"          = "true"
        "--enable-observability-metrics" = "true"
        "--enable-glue-datacatalog"      = "true"
        "--job-bookmark-option"          = "job-bookmark-disable"
        "--job-language"                 = "python"
        "--TempDir"                      = "s3://${local.glue_assets_bucket_name}/temporary/"
        "--datalake-formats"             = "delta"
        "--INPUT_PATH"                   = "s3://${local.data_processed_bucket}/inference_logs/"
        "--DELTA_PATH"                   = "s3://${local.data_processed_bucket}/transformed_zone/"
      }
    }
  ]

  # Triggers SCHEDULED
  scheduled_triggers = [
    {
      name     = "trigger-weekly-training-${var.environment}"
      schedule = "cron(0 8 ? * SUN *)"
      job_name = "job_training_test_1"
    }
  ]

  # Triggers CONDITIONAL
  conditional_triggers = [
    {
      name            = "trigger-enrich-after-training-${var.environment}"
      job_name        = "job_backfill_enrich"
      condition_job   = "job_training_test_1"
      condition_state = "SUCCEEDED"
    }
  ]

  tags = var.common_tags
}
```

### Uso Basico (Apenas IAM Role + Database)

```hcl
module "glue" {
  source = "../../../modules/glue"

  project_name  = "elo-fraud"
  environment   = "dev"
  database_name = "elo_fraud_dev_db"
  role_name     = "elo-fraud-glue-role-dev"

  # Nao criar bucket ou jobs
  create_assets_bucket = false
  scripts              = []
  jobs                 = []
  scheduled_triggers   = []
  conditional_triggers = []
}
```

---

## Variaveis

### Gerais

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `project_name` | `string` | - | sim | Nome do projeto |
| `environment` | `string` | - | sim | Ambiente (dev, staging, prod) |
| `tags` | `map(string)` | `{}` | nao | Tags comuns |

### IAM Role

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `role_name` | `string` | - | sim | Nome da IAM Role |

### Database

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `create_database` | `bool` | `true` | nao | Criar Glue Database |
| `database_name` | `string` | - | sim | Nome do database |

### S3 Assets

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `create_assets_bucket` | `bool` | `true` | nao | Criar bucket S3 |
| `assets_bucket_name` | `string` | `""` | nao | Nome do bucket |

### Scripts

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `scripts` | `list(object)` | `[]` | nao | Lista de scripts para upload |

Estrutura do objeto script:
```hcl
{
  name       = string  # Identificador do script
  s3_key     = string  # Chave no S3
  local_path = string  # Caminho local do arquivo
}
```

### Jobs

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `jobs` | `list(object)` | `[]` | nao | Lista de Glue Jobs |

Estrutura do objeto job:
```hcl
{
  name                = string       # Nome do job
  description         = string       # Descricao
  script_name         = string       # Referencia scripts[].name
  glue_version        = string       # Ex: "5.0"
  worker_type         = string       # G.1X, G.2X, etc
  number_of_workers   = number       # Numero de workers
  timeout             = number       # Timeout em minutos
  max_retries         = number       # Retentativas
  max_concurrent_runs = number       # Runs simultaneas
  default_arguments   = map(string)  # Argumentos EXPLICITOS
}
```

### Triggers

| Variavel | Tipo | Default | Obrigatorio | Descricao |
|----------|------|---------|:-----------:|-----------|
| `scheduled_triggers` | `list(object)` | `[]` | nao | Triggers SCHEDULED |
| `conditional_triggers` | `list(object)` | `[]` | nao | Triggers CONDITIONAL |

Estrutura scheduled_trigger:
```hcl
{
  name     = string  # Nome do trigger
  schedule = string  # Expressao cron
  job_name = string  # Job a executar
}
```

Estrutura conditional_trigger:
```hcl
{
  name            = string  # Nome do trigger
  job_name        = string  # Job a executar
  condition_job   = string  # Job que dispara
  condition_state = string  # SUCCEEDED, FAILED, etc
}
```

---

## Outputs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `role_arn` | `string` | ARN da IAM Role |
| `role_name` | `string` | Nome da IAM Role |
| `assets_bucket_id` | `string` | ID do bucket S3 |
| `assets_bucket_arn` | `string` | ARN do bucket S3 |
| `scripts` | `map(string)` | Map de scripts (nome => s3_key) |
| `job_names` | `list(string)` | Lista de nomes dos jobs |
| `job_arns` | `map(string)` | Map de ARNs dos jobs |
| `scheduled_trigger_names` | `list(string)` | Lista de triggers SCHEDULED |
| `conditional_trigger_names` | `list(string)` | Lista de triggers CONDITIONAL |
| `database_name` | `string` | Nome do Glue Database |

---

## Migracao de Estado

Ao refatorar recursos existentes para usar este modulo, execute o script de migracao:

```bash
cd infra/environments/dev/platform
chmod +x migrate-glue-state.sh
./migrate-glue-state.sh
terraform plan
```

O script usa `terraform state mv` para mover recursos existentes para os novos enderecos do modulo, evitando recriacao de recursos na AWS.

### Mapeamento de Recursos

| Recurso Original | Novo Endereco |
|------------------|---------------|
| `aws_s3_bucket.glue_assets` | `module.glue.aws_s3_bucket.glue_assets[0]` |
| `aws_s3_object.script_training` | `module.glue.aws_s3_object.scripts["training"]` |
| `aws_glue_job.training_landing_to_transformed` | `module.glue.aws_glue_job.jobs["job_training_test_1"]` |
| `aws_glue_trigger.weekly_training_schedule` | `module.glue.aws_glue_trigger.scheduled["trigger-..."]` |

---

## Integracao com Athena

O Glue Catalog Database e compartilhado com Amazon Athena. Tabelas criadas no Glue aparecem automaticamente no Athena e vice-versa.

```sql
-- Tabela criada no Athena aparece no Glue Catalog
SELECT * FROM elo_fraud_staging_db.transaction_results LIMIT 10;
```

---

## Operacoes

### Listar Jobs

```bash
aws glue get-jobs --region us-east-1
```

### Executar Job Manualmente

```bash
aws glue start-job-run \
  --job-name job_training_test_1 \
  --region us-east-1
```

### Ver Status do Job

```bash
aws glue get-job-runs \
  --job-name job_training_test_1 \
  --region us-east-1
```

### Ativar Trigger

```bash
aws glue start-trigger \
  --name trigger-weekly-training-dev \
  --region us-east-1
```

---

## Troubleshooting

### Erro: Job falha com Access Denied

**Causa**: IAM Role sem permissao no bucket.

**Solucao**: Verificar policies da role:
```bash
aws iam list-attached-role-policies \
  --role-name elo-fraud-glue-role-dev
```

### Erro: Script not found

**Causa**: Script nao foi uploadado para S3.

**Solucao**: Verificar se o script existe:
```bash
aws s3 ls s3://aws-glue-assets-123456-us-east-1/scripts/
```

### Erro: Trigger nao dispara

**Causa**: Trigger nao esta ativado.

**Solucao**: Ativar o trigger:
```bash
aws glue start-trigger --name trigger-weekly-training-dev
```

---

## Notas

- Tags sao removidas de alguns recursos devido a SCP que bloqueia tagging
- O modulo suporta multiplos jobs e triggers via `for_each`
- Cada job define seus `default_arguments` explicitamente (sem merge de defaults)
- Isso garante 100% paridade com a configuracao atual na AWS
