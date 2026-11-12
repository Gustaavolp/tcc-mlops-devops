# -----------------------------------------------------------------------------
# Storage & Data Configuration
# -----------------------------------------------------------------------------
# Este arquivo contém módulos de armazenamento e dados: DynamoDB, SQS, ECR
# S3 foi movido para a stack Foundation

# -----------------------------------------------------------------------------
# DynamoDB Module
# -----------------------------------------------------------------------------
# HABILITADO (2025-11-13): Cache de transações recentes para feature enrichment
# Custo estimado: ~$0/mês em staging (PAY_PER_REQUEST sem tráfego)

module "dynamodb" {
  source = "../../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  # Schema - 3DS Transaction Data (atualizado 2026-02-02)
  table_name_suffix = "customer-recent-tx"
  hash_key          = var.dynamodb_hash_key  # PK: Account ID
  hash_key_type     = "S"                    # String
  range_key         = var.dynamodb_range_key # SK: 3DS Server Transaction ID
  range_key_type    = "S"                    # String

  # Segurança - STAGING
  point_in_time_recovery_enabled = false # Não necessário em staging
  deletion_protection_enabled    = false # Permite deletar em staging

  tags = var.common_tags
}

# SQS Module - DESABILITADO (não necessário para MLflow + SageMaker Studio)
# Para habilitar: descomentar este bloco
# Economia: ~$0.30/mês

# -----------------------------------------------------------------------------
# SQS Module
# -----------------------------------------------------------------------------

module "sqs" {
  source = "../../../modules/sqs"

  environment = var.environment

  # Queue names (FIFO - sempre terminam com .fifo)
  # "resultset" = termo usado na documentação para dados TE40 assíncronos
  queue_name = "${var.project_name}-resultset-${var.environment}.fifo"
  dlq_name   = "${var.project_name}-resultset-${var.environment}-dlq.fifo"

  # FIFO Configuration (requisito do projeto)
  fifo_queue                  = var.sqs_fifo_queue
  content_based_deduplication = var.sqs_content_based_deduplication

  # Timing (valores definidos em terraform.tfvars)
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  message_retention_seconds  = var.sqs_message_retention_seconds
  receive_wait_time_seconds  = var.sqs_receive_wait_time_seconds
  delay_seconds              = var.sqs_delay_seconds
  max_message_size           = var.sqs_max_message_size

  # DLQ
  max_receive_count             = var.sqs_max_receive_count
  dlq_message_retention_seconds = var.sqs_dlq_message_retention_seconds

  # Alarms (valores definidos em terraform.tfvars)
  alarm_queue_depth_threshold  = var.sqs_alarm_queue_depth_threshold
  alarm_age_threshold_seconds  = var.sqs_alarm_age_threshold_seconds
  dlq_alarm_threshold          = var.sqs_dlq_alarm_threshold
  alarm_evaluation_periods     = var.sqs_alarm_evaluation_periods
  alarm_period_seconds         = var.sqs_alarm_period_seconds
  dlq_alarm_evaluation_periods = var.sqs_dlq_alarm_evaluation_periods
  dlq_alarm_period_seconds     = var.sqs_dlq_alarm_period_seconds

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# ECR Module
# -----------------------------------------------------------------------------

module "ecr" {
  source = "../../../modules/ecr"

  environment = var.environment

  # ==========================================================================
  # Repositórios para Serviços EKS (Kubernetes)
  # ==========================================================================
  inference_repo_name = "${var.project_name}-inference-${var.environment}"
  process_repo_name   = "${var.project_name}-process-${var.environment}"
  model_repo_name     = "${var.project_name}-model-${var.environment}"

  # ==========================================================================
  # Repositórios para Lambdas (Container Image)
  # ==========================================================================
  best_model_register_repo_name = "best-model-register-${var.environment}"
  etl_delta_filter_repo_name    = "etl-delta-filter-${var.environment}"
  training_launcher_repo_name   = "training-launcher-${var.environment}"

  # ==========================================================================
  # Configurações Comuns
  # ==========================================================================
  # Scanning
  enable_image_scanning = true

  # Tags imutáveis (tag = commit, publicada pelo CI/CD); "latest" fica mutável
  # apenas para o bootstrap inicial dos manifestos e das Lambdas.
  image_tag_mutability                   = "IMMUTABLE_WITH_EXCLUSION"
  image_tag_mutability_exclusion_filters = ["latest"]

  # Lifecycle
  max_image_count               = 30 # Manter últimas 30 imagens
  untagged_image_retention_days = 7  # Deletar untagged após 7 dias

  tags = var.common_tags
}
