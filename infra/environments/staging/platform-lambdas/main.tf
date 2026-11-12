# =============================================================================
# Lambda - Register Best Model (Container)
# =============================================================================
# Acionada via S3 Notification quando objetos sao criados no bucket SageMaker.
# Consulta MLflow, identifica melhor modelo baseado em training_f1_score e registra
# no Model Registry.
#
# PRE-REQUISITO: Imagem Docker deve existir no ECR antes de aplicar esta stack.
# O ECR repository e criado pela stack Platform.
#
# Fluxo de deploy:
# 1. Platform stack cria ECR repository
# 2. CI/CD faz build e push da imagem Docker
# 3. Esta stack cria a Lambda function
# =============================================================================

module "lambda_register_best_model" {
  source = "../../../modules/lambda"

  environment = var.environment

  # Nome da função (explícito)
  function_name = "${var.project_name}-register-best-model-${var.environment}"
  description   = "Registra o melhor modelo do MLflow baseado em training_f1_score"

  # Container Image (ECR) - referencia via remote state
  image_uri = "${local.ecr_register_best_model_url}:latest"

  # Configuracoes (valores definidos em terraform.tfvars)
  timeout     = var.lambda_register_best_model_timeout
  memory_size = var.lambda_register_best_model_memory_size

  # Environment Variables (valores definidos em terraform.tfvars)
  environment_variables = {
    # -------------------------------------------------------------------------
    # MLflow Tracking URI (via remote_state da stack MLOps)
    # -------------------------------------------------------------------------
    # Usa o MLflow Tracking Server da stack MLOps automaticamente.
    # Para usar o MLflow App (SageMaker Studio), defina mlflow_tracking_uri
    # no terraform.tfvars com o ARN do MLflow App. Ver data.tf para detalhes.
    # -------------------------------------------------------------------------
    MLFLOW_TRACKING_URI = local.mlflow_uri

    # Model Registry Configuration (valores definidos em terraform.tfvars)
    MODEL_NAME            = var.lambda_register_best_model_model_name
    METRIC_TO_COMPARE     = var.lambda_register_best_model_metric_to_compare
    MLFLOW_BEST_MODEL_RUN = var.lambda_register_best_model_best_model_run
    MLFLOW_TARGET_TAG_KEY = var.lambda_register_best_model_target_tag_key
    MLFLOW_TARGET_TAG     = var.lambda_register_best_model_target_tag

    # Evento de nova versão registrada -> rolling restart da inferência (stack infra/cicd)
    ENVIRONMENT             = var.environment
    PROMOTION_EVENT_SOURCE  = "elo-fraud.mlops"
    PROMOTION_EVENT_BUS     = "default"
    PUBLISH_PROMOTION_EVENT = "true"
  }

  # IAM (AWS Managed Policies - SCP bloqueia custom policies)
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
  ]

  # Publicação do evento de nova versão registrada
  inline_policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["events:PutEvents"]
      Resource = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:event-bus/default"
    }]
  })

  # S3 Trigger - SageMaker Bucket
  # Bucket criado automaticamente pelo SageMaker: sagemaker-{region}-{account_id}
  enable_s3_trigger      = true
  s3_trigger_bucket_name = "sagemaker-${var.aws_region}-${var.aws_account_id}"
  s3_trigger_events      = ["s3:ObjectCreated:*"]

  tags = var.common_tags
}


# =============================================================================
# Lambda - ETL Delta Filter (Container Image)
# =============================================================================
# Filtra dados do S3 para gerar delta incremental usando Delta Lake.
# Trigger: EventBridge (Glue Job SUCCEEDED)
# Container Image: etl-delta-filter-staging (ECR gerenciado pela stack Platform)
# Dependencias: deltalake, pyarrow, python-dateutil
# =============================================================================

module "lambda_etl_delta_filter" {
  source = "../../../modules/lambda"

  environment = var.environment

  function_name = "${var.project_name}-etl-delta-filter-${var.environment}"
  description   = "Filtra dados do S3 para gerar delta incremental usando Delta Lake"

  image_uri   = "${local.ecr_etl_delta_filter_url}:latest"
  timeout     = var.lambda_etl_timeout
  memory_size = var.lambda_etl_memory_size

  log_retention_days = var.lambda_etl_log_retention_days

  environment_variables = {
    LOG_LEVEL     = "INFO"
    SOURCE_BUCKET = local.s3_processed_bucket_id
    TARGET_BUCKET = local.s3_processed_bucket_id
  }

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
  ]

  # S3 trigger gerenciado fora do modulo (bucket compartilhado com training-launcher)
  enable_s3_trigger = false

  tags = var.common_tags
}


# =============================================================================
# Lambda - Training Launcher (Container Image)
# =============================================================================
# Lanca jobs de treinamento SageMaker usando ModelTrainer SDK.
# Trigger: S3 Notification em training_zone/ (gerenciado fora do modulo)
# Container Image: training-launcher-staging (ECR gerenciado pela stack Platform)
# Dependencias: sagemaker SDK
# =============================================================================

module "lambda_training_launcher" {
  source = "../../../modules/lambda"

  environment = var.environment

  function_name = "${var.project_name}-training-launcher-${var.environment}"
  description   = "Lanca jobs de treinamento SageMaker via ModelTrainer SDK"

  image_uri   = "${local.ecr_training_launcher_url}:latest"
  timeout     = var.lambda_training_launcher_timeout
  memory_size = var.lambda_training_launcher_memory_size

  log_retention_days = var.lambda_training_launcher_log_retention_days

  environment_variables = {
    LOG_LEVEL              = "INFO"
    MLFLOW_URI             = local.mlflow_uri
    MLFLOW_EXPERIMENT_NAME = var.lambda_training_launcher_experiment_name
    SAGEMAKER_ROLE         = local.mlflow_execution_role_arn
    TRAINING_IMAGE         = "${local.ecr_model_url}:latest" # fallback
    TRAINING_IMAGE_PARAM   = aws_ssm_parameter.training_image.name
    DATA_S3_PATH           = "s3://${local.s3_processed_bucket_id}/${var.s3_prefix_training_zone}/"
    DATASET_NAME           = var.lambda_training_launcher_dataset_name
    IS_PROD                = var.environment == "prod" ? "True" : "False"
    INSTANCE_TYPE          = var.lambda_training_launcher_instance_type
  }

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
  ]

  # Leitura do parâmetro com a imagem de treino vigente (atualizado pelo CI/CD)
  inline_policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter"]
      Resource = aws_ssm_parameter.training_image.arn
    }]
  })

  # S3 trigger gerenciado fora do modulo (bucket compartilhado com etl-delta-filter)
  enable_s3_trigger = false

  tags = var.common_tags
}


# =============================================================================
# S3 Triggers (fora do modulo - bucket compartilhado)
# =============================================================================
# AWS permite apenas UMA aws_s3_bucket_notification por bucket.
# Training Launcher triga em training_zone/ quando a Lambda ETL gera Parquets.
# ETL Delta Filter agora usa EventBridge (ver secao abaixo).
# =============================================================================

resource "aws_lambda_permission" "training_launcher_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_training_launcher.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = local.s3_processed_bucket_arn
}

resource "aws_s3_bucket_notification" "processed_bucket" {
  bucket = local.s3_processed_bucket_id

  # Training Launcher - trigger em training_zone/
  lambda_function {
    lambda_function_arn = module.lambda_training_launcher.function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "${var.s3_prefix_training_zone}/"
    filter_suffix       = ".parquet"
  }

  depends_on = [
    aws_lambda_permission.training_launcher_s3,
  ]
}


# =============================================================================
# EventBridge - Glue Job SUCCEEDED -> ETL Delta Filter
# =============================================================================
# Dispara a Lambda ETL Delta Filter quando o Glue Job de training completa
# com sucesso. Substitui o antigo S3 trigger em landing_zone/ que ficou
# orfao apos a migracao do Firehose para inference_logs/.
#
# Fluxo: Glue Job (transformed_zone) -> SUCCEEDED -> EventBridge -> Lambda ETL
# =============================================================================

resource "aws_cloudwatch_event_rule" "glue_job_succeeded" {
  name        = "${var.project_name}-glue-succeeded-${var.environment}"
  description = "Dispara Lambda ETL quando Glue Job ${var.glue_training_job_name} completa com sucesso"

  event_pattern = jsonencode({
    source      = ["aws.glue"]
    detail-type = ["Glue Job State Change"]
    detail = {
      jobName = [var.glue_training_job_name]
      state   = ["SUCCEEDED"]
    }
  })
}

resource "aws_cloudwatch_event_target" "etl_delta_filter" {
  rule = aws_cloudwatch_event_rule.glue_job_succeeded.name
  arn  = module.lambda_etl_delta_filter.function_arn
}

resource "aws_lambda_permission" "etl_delta_filter_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_etl_delta_filter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.glue_job_succeeded.arn
}


# =============================================================================
# Imagem de treino vigente (lida pela training-launcher)
# =============================================================================
# O pipeline de CI/CD da imagem de treinamento atualiza o valor com a tag
# imutável do commit; o Terraform só cria o parâmetro e não reverte o valor.
# =============================================================================

resource "aws_ssm_parameter" "training_image" {
  name        = "/${var.project_name}/${var.environment}/training-image"
  description = "Imagem do SageMaker Training Job usada pela training-launcher"
  type        = "String"
  value       = "${local.ecr_model_url}:latest"

  lifecycle {
    ignore_changes = [value]
  }
}

data "aws_caller_identity" "current" {}
