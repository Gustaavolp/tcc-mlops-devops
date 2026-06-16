# =============================================================================
# TERRAFORM VARIABLES - MLOPS DEV (us-east-1)
# =============================================================================

# General
project_name       = "elo-fraud"
environment        = "dev"
mlflow_environment = "dev"
aws_region         = "us-east-1"

# MLflow Configuration
tracking_server_size            = "Small"
mlflow_version                  = "3.0"
weekly_maintenance_window_start = "Sun:03:00"
log_retention_days              = 7

# SageMaker Studio
default_notebook_instance_type = "ml.t3.medium"
idle_timeout_in_minutes        = 60
sagemaker_user_profile_name    = "elo-fraud-ml-user"

# SageMaker Studio Options
app_network_access_type      = "PublicInternetOnly"
lifecycle_management_enabled = "ENABLED"
notebook_output_option       = "Allowed"

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "MLOps"
  Region      = "us-east-1"
}
