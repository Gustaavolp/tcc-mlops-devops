# =============================================================================
# VARIABLES - PLATFORM LAMBDAS STACK
# =============================================================================
# Este arquivo declara as variaveis da stack.
# Os valores sao definidos em terraform.tfvars
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente"
  type        = string
}

variable "aws_region" {
  description = "Regiao AWS"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "common_tags" {
  description = "Tags comuns aplicadas a todos os recursos"
  type        = map(string)
}

# -----------------------------------------------------------------------------
# MLflow Configuration
# -----------------------------------------------------------------------------

variable "mlflow_tracking_uri" {
  description = "ARN do MLflow App (criado automaticamente pelo SageMaker Studio)"
  type        = string
}

# -----------------------------------------------------------------------------
# Lambda Register Best Model Configuration
# -----------------------------------------------------------------------------

variable "lambda_register_best_model_timeout" {
  description = "Timeout em segundos da Lambda Register Best Model"
  type        = number
}

variable "lambda_register_best_model_memory_size" {
  description = "Memoria em MB da Lambda Register Best Model"
  type        = number
}

variable "lambda_register_best_model_model_name" {
  description = "Nome do modelo no MLflow Registry"
  type        = string
}

variable "lambda_register_best_model_metric_to_compare" {
  description = "Metrica para comparacao de modelos (ex: metrics.f1_oot)"
  type        = string
}

variable "lambda_register_best_model_best_model_run" {
  description = "Nome do run do melhor modelo no MLflow"
  type        = string
}

variable "lambda_register_best_model_target_tag_key" {
  description = "Chave da tag de destino no MLflow Registry"
  type        = string
}

variable "lambda_register_best_model_target_tag" {
  description = "Valor da tag de destino no MLflow Registry"
  type        = string
}

# -----------------------------------------------------------------------------
# Lambda ETL Delta Filter Configuration
# -----------------------------------------------------------------------------

variable "lambda_etl_timeout" {
  description = "Timeout em segundos da Lambda ETL Delta Filter"
  type        = number
}

variable "lambda_etl_memory_size" {
  description = "Memoria em MB da Lambda ETL Delta Filter"
  type        = number
}

variable "lambda_etl_log_retention_days" {
  description = "Dias de retencao dos logs da Lambda ETL no CloudWatch"
  type        = number
}

# -----------------------------------------------------------------------------
# Lambda Training Launcher Configuration
# -----------------------------------------------------------------------------

variable "lambda_training_launcher_timeout" {
  description = "Timeout em segundos da Lambda Training Launcher"
  type        = number
}

variable "lambda_training_launcher_memory_size" {
  description = "Memoria em MB da Lambda Training Launcher"
  type        = number
}

variable "lambda_training_launcher_log_retention_days" {
  description = "Dias de retencao dos logs da Lambda Training Launcher no CloudWatch"
  type        = number
}

variable "lambda_training_launcher_experiment_name" {
  description = "Nome do experimento MLflow para training jobs"
  type        = string
}

variable "lambda_training_launcher_dataset_name" {
  description = "Nome do dataset para training jobs"
  type        = string
}

variable "lambda_training_launcher_instance_type" {
  description = "Tipo de instancia SageMaker para training jobs"
  type        = string
}

# -----------------------------------------------------------------------------
# Glue Job Configuration (para EventBridge trigger)
# -----------------------------------------------------------------------------

variable "glue_training_job_name" {
  description = "Nome do Glue Job de training (usado no EventBridge para disparar Lambda ETL)"
  type        = string
}

# -----------------------------------------------------------------------------
# Data Lake S3 Prefixes
# -----------------------------------------------------------------------------

variable "s3_prefix_training_zone" {
  description = "Prefixo S3 para dados de treinamento"
  type        = string
}
