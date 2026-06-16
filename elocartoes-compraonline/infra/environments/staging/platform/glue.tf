# -----------------------------------------------------------------------------
# Glue Configuration - ETL Infrastructure
# -----------------------------------------------------------------------------
# Provisiona infraestrutura completa para Glue ETL via módulo:
# - S3 Bucket para assets (scripts, logs, temp files)
# - IAM Role com permissões necessárias
# - Script Python centralizado em glue/ na raiz do projeto
# - Upload automático do script para S3
# - ETL Job para processamento de dados
# - Trigger para agendamento
#
# Pipeline ETL:
# 1. job_training_test_1: inference_logs -> transformed_zone (merge)
#
# Schedule: Domingo 08:00 UTC (05:00 BRT)
#
# Para alterar scripts ETL:
# 1. Editar arquivo em glue/ (raiz do projeto)
# 2. Criar PR no GitHub
# 3. Após aprovação, executar terraform apply
# -----------------------------------------------------------------------------

locals {
  # Bucket name seguindo padrão AWS
  glue_assets_bucket_name = "aws-glue-assets-${var.aws_account_id}-${var.aws_region}"

  # Caminho local dos scripts (compartilhados entre ambientes)
  glue_scripts_local_path = "${path.module}/../../../../glue"

  # Bucket de dados processados (usa project_name para consistencia)
  data_processed_bucket = "${var.project_name}-data-processed-${var.environment}-${var.aws_account_id}"
}

# -----------------------------------------------------------------------------
# Glue Module
# -----------------------------------------------------------------------------

module "glue" {
  source = "../../../modules/glue"

  # IAM Role
  role_name = "${var.project_name}-glue-role-${var.environment}"

  # S3 Assets Bucket
  assets_bucket_name = local.glue_assets_bucket_name

  # Script ETL
  script_s3_key     = "scripts/job_training_test_1.py"
  script_local_path = "${local.glue_scripts_local_path}/job_training_test_1.py"

  # Glue Job (valores de configuracao definidos em terraform.tfvars)
  job_name            = var.glue_training_job_name
  job_description     = "Merge dados de inference_logs para transformed_zone (inferencias e feedbacks)"
  glue_version        = var.glue_version
  worker_type         = var.glue_worker_type
  number_of_workers   = var.glue_number_of_workers
  timeout             = var.glue_job_timeout
  max_retries         = var.glue_max_retries
  max_concurrent_runs = 1
  default_arguments = {
    "--enable-metrics"               = "true"
    "--spark-event-logs-path"        = "s3://${local.glue_assets_bucket_name}/sparkHistoryLogs/"
    "--enable-job-insights"          = "true"
    "--enable-observability-metrics" = "true"
    "--enable-glue-datacatalog"      = "true"
    "--job-bookmark-option"          = "job-bookmark-enable"
    "--job-language"                 = "python"
    "--TempDir"                      = "s3://${local.glue_assets_bucket_name}/temporary/"
    "--datalake-formats"             = "delta"
    "--INPUT_PATH"                   = "s3://${local.data_processed_bucket}/${var.s3_prefix_inference_logs}/"
    "--OUTPUT_PATH"                  = "s3://${local.data_processed_bucket}/${var.s3_prefix_transformed_zone}/"
  }

  # Trigger SCHEDULED
  trigger_name     = "trigger-weekly-training-${var.environment}"
  trigger_schedule = var.glue_training_schedule

}
