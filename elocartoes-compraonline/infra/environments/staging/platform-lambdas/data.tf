# =============================================================================
# Data Sources - Remote State References
# =============================================================================
# Le outputs de outras stacks para obter valores dinamicos.
# =============================================================================

# -----------------------------------------------------------------------------
# Remote State: Platform
# -----------------------------------------------------------------------------
# Obtem URLs dos ECR repositories criados pela stack Platform.

data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "staging/platform/terraform.tfstate"
    region = "us-east-1"
  }
}

# -----------------------------------------------------------------------------
# Remote State: Foundation
# -----------------------------------------------------------------------------
# Obtem S3 buckets (processed) para triggers e environment variables das Lambdas.

data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "staging/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

# -----------------------------------------------------------------------------
# Remote State: MLOps
# -----------------------------------------------------------------------------
# Obtem MLflow Tracking Server ARN e SageMaker Execution Role para
# training-launcher Lambda.

data "terraform_remote_state" "mlops" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "staging/mlops/terraform.tfstate"
    region = "us-east-1"
  }
}

# -----------------------------------------------------------------------------
# Locals - Valores das outras stacks
# -----------------------------------------------------------------------------

locals {
  # ECR Repositories (da stack Platform)
  ecr_register_best_model_url = data.terraform_remote_state.platform.outputs.ecr_register_best_model_url
  ecr_etl_delta_filter_url    = data.terraform_remote_state.platform.outputs.ecr_etl_delta_filter_url
  ecr_training_launcher_url   = data.terraform_remote_state.platform.outputs.ecr_training_launcher_url
  ecr_model_url               = data.terraform_remote_state.platform.outputs.ecr_model_repository_url

  # S3 Buckets (da stack Foundation)
  s3_processed_bucket_id  = data.terraform_remote_state.foundation.outputs.s3_processed_bucket_id
  s3_processed_bucket_arn = data.terraform_remote_state.foundation.outputs.s3_processed_bucket_arn

  # MLOps - MLflow (da stack MLOps)
  mlflow_tracking_server_arn = data.terraform_remote_state.mlops.outputs.mlflow_tracking_server_arn
  mlflow_execution_role_arn  = data.terraform_remote_state.mlops.outputs.mlflow_execution_role_arn

  # -------------------------------------------------------------------------
  # MLflow URI final para as Lambdas
  # -------------------------------------------------------------------------
  # Por padrao, usa o MLflow Tracking Server da stack MLOps (via remote_state).
  # Para usar o MLflow App (criado pelo SageMaker Studio), defina
  # mlflow_tracking_uri no terraform.tfvars com o ARN do MLflow App.
  # Exemplo: mlflow_tracking_uri = "arn:aws:sagemaker:sa-east-1:888577064416:mlflow-app/app-XXXXXXXXXX"
  # -------------------------------------------------------------------------
  mlflow_uri = var.mlflow_tracking_uri != "" ? var.mlflow_tracking_uri : local.mlflow_tracking_server_arn
}
