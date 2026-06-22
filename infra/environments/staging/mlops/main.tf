# =============================================================================
# MLOPS STACK - STAGING (sa-east-1)
# =============================================================================
# Esta stack contém recursos de Machine Learning Operations:
# - MLflow Tracking Server (Managed by SageMaker)
# - SageMaker Studio Domain
#
# Recursos criados:
# - MLflow Tracking Server `elo-fraud-mlflow-staging`
# - S3 Bucket para artifacts
# - IAM Role com permissões completas
# - CloudWatch Log Group
# - SageMaker Studio Domain
# =============================================================================

# -----------------------------------------------------------------------------
# MLflow Tracking Server
# -----------------------------------------------------------------------------
module "mlflow" {
  source = "../../../modules/mlflow"

  environment = var.mlflow_environment # "staging"

  # Nomes dos recursos (explícitos)
  tracking_server_name = "${var.project_name}-mlflow-${var.mlflow_environment}"
  artifact_bucket_name = "${var.project_name}-mlflow-artifacts-${var.mlflow_environment}-${local.aws_account_id}"
  execution_role_name  = "${var.project_name}-mlflow-${var.mlflow_environment}-execution-role"
  log_group_name       = "/aws/sagemaker/mlflow/${var.project_name}-mlflow-${var.mlflow_environment}"

  tracking_server_size            = var.tracking_server_size
  mlflow_version                  = var.mlflow_version
  weekly_maintenance_window_start = var.weekly_maintenance_window_start
  log_retention_days              = var.log_retention_days

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# SageMaker Studio Domain
# -----------------------------------------------------------------------------
module "sagemaker_studio" {
  source = "../../../modules/sagemaker-studio"

  # Nomes dos recursos (explícitos)
  domain_name         = "${var.project_name}-studio-${var.mlflow_environment}"
  execution_role_name = "${var.project_name}-studio-${var.mlflow_environment}-execution-role"
  log_group_name      = "/aws/sagemaker/studio/${var.project_name}-studio-${var.mlflow_environment}"

  # Network Configuration (obrigatorio - subnets privadas para modo VpcOnly)
  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnet_ids
  vpc_cidr   = local.vpc_cidr

  default_notebook_instance_type = var.default_notebook_instance_type

  idle_timeout_in_minutes = var.idle_timeout_in_minutes
  log_retention_days      = var.log_retention_days

  # Studio Options
  app_network_access_type      = var.app_network_access_type
  lifecycle_management_enabled = var.lifecycle_management_enabled
  notebook_output_option       = var.notebook_output_option

  # User Profiles
  user_profiles = [
    {
      name               = var.sagemaker_user_profile_name
      execution_role_arn = module.mlflow.execution_role_arn
    }
  ]

  tags = var.common_tags

  depends_on = [module.mlflow]
}
