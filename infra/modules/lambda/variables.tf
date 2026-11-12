# -----------------------------------------------------------------------------
# Lambda Module Variables (Container Image Only)
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, stg, prd)"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Lambda Configuration
# -----------------------------------------------------------------------------

variable "function_name" {
  description = "Nome da função Lambda"
  type        = string
}

variable "description" {
  description = "Descrição da função Lambda"
  type        = string
  default     = ""
}

variable "image_uri" {
  description = "URI da imagem ECR para Lambda (container image)"
  type        = string
}

variable "timeout" {
  description = "Timeout em segundos"
  type        = number
  default     = 60
}

variable "memory_size" {
  description = "Memória em MB"
  type        = number
  default     = 256
}

# -----------------------------------------------------------------------------
# Environment Variables
# -----------------------------------------------------------------------------

variable "environment_variables" {
  description = "Variáveis de ambiente da Lambda"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# IAM
# -----------------------------------------------------------------------------

variable "managed_policy_arns" {
  description = "Lista de ARNs de AWS Managed Policies"
  type        = list(string)
  default     = []
}

variable "inline_policy_json" {
  description = "Política IAM inline adicional (JSON) com permissões específicas da função; null para nenhuma"
  type        = string
  default     = null
}

# -----------------------------------------------------------------------------
# S3 Trigger
# -----------------------------------------------------------------------------

variable "enable_s3_trigger" {
  description = "Habilitar trigger via S3 Notification"
  type        = bool
  default     = false
}

variable "s3_trigger_bucket_name" {
  description = "Nome do bucket S3 que dispara a Lambda"
  type        = string
  default     = ""
}

variable "s3_trigger_events" {
  description = "Lista de eventos S3 que disparam a Lambda"
  type        = list(string)
  default     = ["s3:ObjectCreated:*"]
}

variable "s3_trigger_filter_prefix" {
  description = "Filtro de prefixo para eventos S3 (opcional)"
  type        = string
  default     = null
}

variable "s3_trigger_filter_suffix" {
  description = "Filtro de sufixo para eventos S3 (opcional)"
  type        = string
  default     = null
}

# -----------------------------------------------------------------------------
# CloudWatch Logs
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Dias de retenção dos logs"
  type        = number
  default     = 14
}
