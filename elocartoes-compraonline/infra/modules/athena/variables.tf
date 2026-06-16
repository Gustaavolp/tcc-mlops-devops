# -----------------------------------------------------------------------------
# Athena Module - Variables
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "database_name" {
  description = "Nome do Glue Catalog Database"
  type        = string
}

variable "workgroup_name" {
  description = "Nome do Athena Workgroup"
  type        = string
}

variable "results_bucket_name" {
  description = "Nome do S3 bucket para resultados de queries Athena"
  type        = string
}

variable "tags" {
  description = "Tags comuns para os recursos"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Source Data Configuration
# -----------------------------------------------------------------------------

variable "source_bucket_name" {
  description = "Nome do bucket S3 com os dados do Process Service"
  type        = string
}

# -----------------------------------------------------------------------------
# Athena Configuration
# -----------------------------------------------------------------------------

variable "bytes_scanned_limit" {
  description = "Limite de bytes escaneados por query (controle de custos)"
  type        = number
  default     = 10737418240 # 10 GB
}

variable "force_destroy" {
  description = "Permitir deletar bucket com objetos (apenas dev)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Inference Logs Table Configuration
# -----------------------------------------------------------------------------

variable "inference_logs_prefix" {
  description = "Prefixo dos inference logs no S3 (onde o Firehose escreve)"
  type        = string
  default     = "inference_logs"
}

# -----------------------------------------------------------------------------
# Table Names Configuration
# -----------------------------------------------------------------------------

variable "inference_logs_table_name" {
  description = "Nome da tabela Glue para inference logs (JSON)"
  type        = string
  default     = "inference_logs"
}

# -----------------------------------------------------------------------------
# Partition Projection Configuration
# -----------------------------------------------------------------------------

variable "partition_projection_year_range" {
  description = "Range de anos para partition projection (formato: 'min,max')"
  type        = string
  default     = "2024,2030"

  validation {
    condition     = can(regex("^[0-9]{4},[0-9]{4}$", var.partition_projection_year_range))
    error_message = "partition_projection_year_range deve estar no formato 'YYYY,YYYY' (ex: '2024,2030')"
  }
}
