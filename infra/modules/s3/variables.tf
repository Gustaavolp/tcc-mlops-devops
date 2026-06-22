variable "environment" {
  description = "Ambiente (dev, staging, prd)"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Nomes dos buckets
# -----------------------------------------------------------------------------

variable "raw_bucket_name" {
  description = "Nome do bucket para dados raw (3DS + TE40)"
  type        = string
}

variable "processed_bucket_name" {
  description = "Nome do bucket para dados processados"
  type        = string
}

variable "models_bucket_name" {
  description = "Nome do bucket para artefatos de modelos ML"
  type        = string
}

variable "logs_bucket_name" {
  description = "Nome do bucket para logs centralizados"
  type        = string
}

variable "resources_bucket_name" {
  description = "Nome do bucket para recursos estáticos (templates, configs)"
  type        = string
}

variable "reports_promotion_bucket_name" {
  description = "Nome do bucket para relatórios de promoção"
  type        = string
}

variable "reports_statistics_bucket_name" {
  description = "Nome do bucket para relatórios estatísticos"
  type        = string
}
