# -----------------------------------------------------------------------------
# MLflow Tracking Server Variables
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags comuns para todos os recursos"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Resource Names (explícitos)
# -----------------------------------------------------------------------------

variable "tracking_server_name" {
  description = "Nome do MLflow Tracking Server"
  type        = string
}

variable "artifact_bucket_name" {
  description = "Nome do S3 bucket para artifacts (deve ser globalmente único)"
  type        = string
}

variable "execution_role_name" {
  description = "Nome da IAM Role para execução do MLflow"
  type        = string
}

variable "log_group_name" {
  description = "Nome do CloudWatch Log Group"
  type        = string
}

# -----------------------------------------------------------------------------
# MLflow Configuration
# -----------------------------------------------------------------------------

variable "tracking_server_size" {
  description = "Tamanho do servidor MLflow (Small, Medium, Large)"
  type        = string
  default     = "Small"

  validation {
    condition     = contains(["Small", "Medium", "Large"], var.tracking_server_size)
    error_message = "tracking_server_size deve ser Small, Medium ou Large"
  }
}

variable "mlflow_version" {
  description = "Versão do MLflow a ser utilizada (formato AWS: major.minor, ex: 3.0)"
  type        = string
  default     = "3.0"

  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+(\\.[0-9]+)?$", var.mlflow_version))
    error_message = "mlflow_version deve estar no formato X.Y ou X.Y.Z (ex: 3.0 ou 2.12.1)"
  }
}

variable "weekly_maintenance_window_start" {
  description = "Janela de manutenção semanal no formato ddd:hh24:mi (ex: Sun:03:00)"
  type        = string
  default     = "Sun:03:00"

  validation {
    condition     = can(regex("^(Mon|Tue|Wed|Thu|Fri|Sat|Sun):([01][0-9]|2[0-3]):([0-5][0-9])$", var.weekly_maintenance_window_start))
    error_message = "weekly_maintenance_window_start deve estar no formato ddd:hh24:mi (ex: Sun:03:00)"
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Logs Configuration
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Dias de retenção para logs do CloudWatch"
  type        = number
  default     = 7

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180,
      365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "log_retention_days deve ser um valor válido do CloudWatch (1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653)"
  }
}
