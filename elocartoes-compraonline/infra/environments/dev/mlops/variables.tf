# =============================================================================
# VARIABLES - MLOPS STACK
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

variable "mlflow_environment" {
  description = "Ambiente para o modulo MLflow (dev, stg, prd)"
  type        = string
}

variable "aws_region" {
  description = "Regiao AWS"
  type        = string
}

# -----------------------------------------------------------------------------
# MLflow Configuration
# -----------------------------------------------------------------------------

variable "tracking_server_size" {
  description = "Tamanho do servidor MLflow (Small, Medium, Large)"
  type        = string
}

variable "mlflow_version" {
  description = "Versao do MLflow"
  type        = string
}

variable "weekly_maintenance_window_start" {
  description = "Janela de manutencao semanal (formato: ddd:hh24:mi)"
  type        = string
}

variable "log_retention_days" {
  description = "Dias de retencao para logs do CloudWatch"
  type        = number
}

# -----------------------------------------------------------------------------
# SageMaker Studio Configuration
# -----------------------------------------------------------------------------

variable "default_notebook_instance_type" {
  description = "Tipo de instancia padrao para notebooks"
  type        = string
}

variable "idle_timeout_in_minutes" {
  description = "Minutos de inatividade antes de desligar"
  type        = number
}

variable "sagemaker_user_profile_name" {
  description = "Nome do perfil de usuario SageMaker"
  type        = string
}

# -----------------------------------------------------------------------------
# SageMaker Studio Options
# -----------------------------------------------------------------------------

variable "app_network_access_type" {
  description = "Tipo de acesso de rede do SageMaker Studio (PublicInternetOnly ou VpcOnly)"
  type        = string
}

variable "lifecycle_management_enabled" {
  description = "Gerenciamento de lifecycle para apps ociosos (ENABLED ou DISABLED)"
  type        = string
}

variable "notebook_output_option" {
  description = "Permitir export de outputs de notebooks (Allowed ou Disabled)"
  type        = string
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "common_tags" {
  description = "Tags comuns para todos os recursos"
  type        = map(string)
}
