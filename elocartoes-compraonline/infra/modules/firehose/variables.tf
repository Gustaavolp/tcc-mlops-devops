# -----------------------------------------------------------------------------
# Kinesis Firehose Module - Variables
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, stg, prd)"
  type        = string
}

variable "stream_name" {
  description = "Nome do Firehose Delivery Stream (ex: elo-fraud-inference-firehose-dev)"
  type        = string
}

variable "purpose_description" {
  description = "Descricao do proposito do stream para tags"
  type        = string
  default     = "Transaction Results Batch Delivery"
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# S3 Destination Configuration
# -----------------------------------------------------------------------------

variable "s3_bucket_arn" {
  description = "ARN do bucket S3 de destino"
  type        = string
}

variable "s3_prefix" {
  description = "Prefixo no S3 onde os dados serão escritos (ex: landing_zone)"
  type        = string
  default     = "landing_zone"
}

# -----------------------------------------------------------------------------
# Buffer Configuration
# -----------------------------------------------------------------------------

variable "buffer_size_mb" {
  description = "Tamanho do buffer em MB antes de entregar ao S3"
  type        = number
  default     = 1
}

variable "buffer_interval_seconds" {
  description = "Intervalo em segundos antes de entregar ao S3"
  type        = number
  default     = 60
}

# -----------------------------------------------------------------------------
# Compression Configuration
# -----------------------------------------------------------------------------

variable "compression_format" {
  description = "Formato de compressao dos dados no S3 (UNCOMPRESSED, GZIP, ZIP, Snappy, HADOOP_SNAPPY)"
  type        = string
  default     = "UNCOMPRESSED"

  validation {
    condition     = contains(["UNCOMPRESSED", "GZIP", "ZIP", "Snappy", "HADOOP_SNAPPY"], var.compression_format)
    error_message = "compression_format deve ser: UNCOMPRESSED, GZIP, ZIP, Snappy ou HADOOP_SNAPPY"
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Configuration
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Dias de retencao dos logs do Firehose no CloudWatch"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# CloudWatch Alarm Configuration
# -----------------------------------------------------------------------------

variable "alarm_evaluation_periods" {
  description = "Numero de periodos para avaliar o alarme de entrega"
  type        = number
  default     = 2

  validation {
    condition     = var.alarm_evaluation_periods >= 1
    error_message = "alarm_evaluation_periods deve ser pelo menos 1"
  }
}

variable "alarm_period_seconds" {
  description = "Periodo em segundos para coleta de metricas do alarme"
  type        = number
  default     = 300

  validation {
    condition     = contains([60, 300, 600, 900, 1800, 3600], var.alarm_period_seconds)
    error_message = "alarm_period_seconds deve ser um dos valores validos: 60, 300, 600, 900, 1800, 3600"
  }
}

variable "alarm_delivery_success_threshold" {
  description = "Threshold de sucesso de entrega (1 = 100%%, 0.99 = 99%%, etc.)"
  type        = number
  default     = 1

  validation {
    condition     = var.alarm_delivery_success_threshold >= 0 && var.alarm_delivery_success_threshold <= 1
    error_message = "alarm_delivery_success_threshold deve estar entre 0 e 1"
  }
}

# -----------------------------------------------------------------------------
# S3 Backup Configuration
# -----------------------------------------------------------------------------

variable "s3_backup_mode" {
  description = "Modo de backup S3 (Disabled ou Enabled)"
  type        = string
  default     = "Disabled"

  validation {
    condition     = contains(["Disabled", "Enabled"], var.s3_backup_mode)
    error_message = "s3_backup_mode deve ser Disabled ou Enabled"
  }
}
