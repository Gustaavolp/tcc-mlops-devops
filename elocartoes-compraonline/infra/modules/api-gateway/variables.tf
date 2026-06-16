# -----------------------------------------------------------------------------
# API Gateway Module - Variables
# -----------------------------------------------------------------------------
# Modulo para criar REST API com integracao privada via VPC Link
#
# Arquitetura (trafego interno):
#   Cliente -> API Gateway -> VPC Link -> NLB (privado) -> EKS Pods (porta 8000)
#
# NOTA: Este modulo usa APENAS trafego interno via VPC Link.
# O trafego entre API Gateway e o backend nao passa pela internet publica.
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, stg, prd)"
  type        = string
}

variable "api_name" {
  description = "Nome da API Gateway (ex: elo-fraud-api-dev)"
  type        = string
}

variable "api_description" {
  description = "Descrição da API"
  type        = string
  default     = "API de Autorizacao de Compras Online - Real-time purchase authorization"
}

# -----------------------------------------------------------------------------
# VPC Link Configuration (integracao privada - OBRIGATORIO)
# -----------------------------------------------------------------------------
# Trafego interno via VPC Link para NLB/ALB privado
# Garante que o trafego nao saia para a internet publica
# -----------------------------------------------------------------------------

variable "nlb_arn" {
  description = "ARN do NLB para VPC Link"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:elasticloadbalancing:", var.nlb_arn))
    error_message = "nlb_arn deve ser um ARN valido de Network Load Balancer"
  }
}

variable "nlb_dns_name" {
  description = "DNS name do NLB"
  type        = string
}

# -----------------------------------------------------------------------------
# API Configuration
# -----------------------------------------------------------------------------

variable "endpoint_configuration_type" {
  description = "Tipo de endpoint: REGIONAL, EDGE, PRIVATE"
  type        = string
  default     = "REGIONAL"
  validation {
    condition     = contains(["REGIONAL", "EDGE", "PRIVATE"], var.endpoint_configuration_type)
    error_message = "endpoint_configuration_type must be REGIONAL, EDGE, or PRIVATE"
  }
}

variable "stage_name" {
  description = "Nome do stage (deployment)"
  type        = string
  default     = "v1"
}

variable "enable_access_logs" {
  description = "Habilitar logs de acesso (CloudWatch)"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Dias de retenção dos logs"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# Throttling & Rate Limiting
# -----------------------------------------------------------------------------

variable "throttle_burst_limit" {
  description = "Burst limit de requests (máximo de requests simultâneas)"
  type        = number
  default     = 5000
}

variable "throttle_rate_limit" {
  description = "Rate limit de requests por segundo"
  type        = number
  default     = 10000
}

# -----------------------------------------------------------------------------
# Usage Plan (Rate Limiting por API Key)
# -----------------------------------------------------------------------------

variable "usage_plan_quota_limit" {
  description = "Limite de quota de requests por período"
  type        = number
  default     = 1000000
}

variable "usage_plan_quota_period" {
  description = "Período da quota (DAY, WEEK, MONTH)"
  type        = string
  default     = "MONTH"

  validation {
    condition     = contains(["DAY", "WEEK", "MONTH"], var.usage_plan_quota_period)
    error_message = "usage_plan_quota_period deve ser DAY, WEEK ou MONTH"
  }
}

variable "usage_plan_throttle_burst_limit" {
  description = "Burst limit por API Key"
  type        = number
  default     = 2000
}

variable "usage_plan_throttle_rate_limit" {
  description = "Rate limit por API Key (req/s)"
  type        = number
  default     = 1000
}

# -----------------------------------------------------------------------------
# API Keys
# -----------------------------------------------------------------------------

variable "api_keys" {
  description = "Mapa de API Keys a serem criadas e associadas ao Usage Plan"
  type = map(object({
    enabled     = bool
    description = string
  }))
  default = {}
}

# -----------------------------------------------------------------------------
# Integration Timeouts
# -----------------------------------------------------------------------------

variable "integration_timeout_ms" {
  description = "Timeout em milissegundos para integracao principal (max 29000ms)"
  type        = number
  default     = 29000

  validation {
    condition     = var.integration_timeout_ms >= 50 && var.integration_timeout_ms <= 29000
    error_message = "integration_timeout_ms deve estar entre 50 e 29000 (limite API Gateway)"
  }
}

variable "health_check_timeout_ms" {
  description = "Timeout em milissegundos para health check"
  type        = number
  default     = 5000

  validation {
    condition     = var.health_check_timeout_ms >= 50 && var.health_check_timeout_ms <= 29000
    error_message = "health_check_timeout_ms deve estar entre 50 e 29000 (limite API Gateway)"
  }
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Tags para aplicar aos recursos"
  type        = map(string)
  default     = {}
}
