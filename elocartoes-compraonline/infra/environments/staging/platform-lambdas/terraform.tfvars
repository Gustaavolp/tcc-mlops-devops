# =============================================================================
# TERRAFORM VARIABLES - PLATFORM LAMBDAS STAGING (sa-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "staging"
aws_region     = "sa-east-1"
aws_account_id = "888577064416"

# =============================================================================
# MLflow Configuration
# =============================================================================
# NOTA: O MLflow App (arn:...:mlflow-app/app-XXX) e diferente do MLflow Tracking
# Server (arn:...:mlflow-tracking-server/nome) gerenciado pelo Terraform.
#
# O MLflow App e:
# - Criado AUTOMATICAMENTE pelo SageMaker Studio Domain
# - Serverless (sem sizing, auto-scaling)
# - Sem custo adicional
# - NAO possui recurso Terraform para gerenciamento
#
# O ARN e estavel apos a criacao do Studio Domain e nao muda.
# Se o Studio Domain for recriado, este ARN precisara ser atualizado.
# =============================================================================
mlflow_tracking_uri = "arn:aws:sagemaker:sa-east-1:888577064416:mlflow-app/app-PLACEHOLDER"

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "staging"
  ManagedBy   = "Terraform"
  Stack       = "Platform-Lambdas"
  Region      = "sa-east-1"
}

# =============================================================================
# Lambda Register Best Model Configuration
# =============================================================================
lambda_register_best_model_timeout     = 300 # 5 minutos
lambda_register_best_model_memory_size = 512 # MB

# MLflow Model Registry Configuration
lambda_register_best_model_model_name        = "Felicidade"     # Nome do modelo no registry
lambda_register_best_model_metric_to_compare = "metrics.f1_oot" # Metrica para comparacao
lambda_register_best_model_best_model_run    = "best_estimator" # Nome do run
lambda_register_best_model_target_tag_key    = "stage"          # Chave da tag
lambda_register_best_model_target_tag        = "prod"           # Valor da tag

# =============================================================================
# Lambda ETL Delta Filter Configuration
# =============================================================================
lambda_etl_timeout            = 900   # 15 minutos - processamento Delta Lake
lambda_etl_memory_size        = 10240 # 10 GB - necessario para pyarrow/deltalake
lambda_etl_log_retention_days = 14    # Dias de retencao dos logs

# =============================================================================
# Lambda Training Launcher Configuration
# =============================================================================
lambda_training_launcher_timeout            = 300                   # 5 minutos - apenas lanca jobs
lambda_training_launcher_memory_size        = 512                   # 512 MB - sagemaker SDK
lambda_training_launcher_log_retention_days = 14                    # Dias de retencao dos logs
lambda_training_launcher_experiment_name    = "classificacao_6.0.0" # Nome do experimento MLflow
lambda_training_launcher_dataset_name       = "gold"                # Nome do dataset
lambda_training_launcher_instance_type      = "ml.r5.4xlarge"       # Instancia SageMaker para training

# =============================================================================
# Glue Job Configuration (EventBridge trigger)
# =============================================================================
glue_training_job_name = "job_training_test_1" # Glue Job que dispara Lambda ETL via EventBridge

# =============================================================================
# Data Lake S3 Prefixes
# =============================================================================
s3_prefix_training_zone = "training_zone" # Dados para treinamento (parquet)
