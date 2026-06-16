# =============================================================================
# NLB Module - Variables
# =============================================================================
# Variaveis para configuracao do Network Load Balancer
# Usado para integracao com VPC Link do API Gateway
# =============================================================================

# -----------------------------------------------------------------------------
# Identificacao
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "name" {
  description = "Nome do NLB"
  type        = string
}

# -----------------------------------------------------------------------------
# Rede
# -----------------------------------------------------------------------------

variable "vpc_id" {
  description = "ID da VPC onde o NLB sera criado"
  type        = string
}

variable "subnet_ids" {
  description = "Lista de IDs de subnets PRIVADAS para o NLB (minimo 2 AZs recomendado)"
  type        = list(string)
}

# -----------------------------------------------------------------------------
# Target
# -----------------------------------------------------------------------------

variable "target_group_name" {
  description = "Nome do Target Group"
  type        = string
}

variable "target_port" {
  description = "Porta do target para encaminhar trafego (porta do servico nos pods)"
  type        = number
  default     = 80
}

variable "deregistration_delay" {
  description = "Tempo em segundos para drenar conexoes ao remover targets"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# Listener
# -----------------------------------------------------------------------------

variable "listener_port" {
  description = "Porta do listener NLB (deve corresponder a porta do VPC Link)"
  type        = number
  default     = 80
}

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# NLB faz health check HTTP para verificar saude dos pods
# Path deve corresponder ao endpoint de health da aplicacao
# -----------------------------------------------------------------------------

variable "health_check_path" {
  description = "Path para health check HTTP (ex: /health)"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Intervalo entre health checks em segundos (minimo 10 para NLB)"
  type        = number
  default     = 30

  validation {
    condition     = var.health_check_interval >= 10 && var.health_check_interval <= 300
    error_message = "health_check_interval deve estar entre 10 e 300 segundos"
  }
}

variable "health_check_timeout" {
  description = "Timeout do health check em segundos (deve ser menor que interval)"
  type        = number
  default     = 10

  validation {
    condition     = var.health_check_timeout >= 2 && var.health_check_timeout <= 120
    error_message = "health_check_timeout deve estar entre 2 e 120 segundos"
  }
}

variable "healthy_threshold" {
  description = "Numero de health checks consecutivos para considerar healthy"
  type        = number
  default     = 3

  validation {
    condition     = var.healthy_threshold >= 2 && var.healthy_threshold <= 10
    error_message = "healthy_threshold deve estar entre 2 e 10"
  }
}

variable "unhealthy_threshold" {
  description = "Numero de health checks consecutivos para considerar unhealthy"
  type        = number
  default     = 3

  validation {
    condition     = var.unhealthy_threshold >= 2 && var.unhealthy_threshold <= 10
    error_message = "unhealthy_threshold deve estar entre 2 e 10"
  }
}

# -----------------------------------------------------------------------------
# NLB Attributes
# -----------------------------------------------------------------------------

variable "enable_cross_zone_load_balancing" {
  description = "Habilitar balanceamento cross-zone (recomendado para alta disponibilidade)"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Habilitar protecao contra delecao acidental (recomendado para producao)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Tags adicionais para os recursos"
  type        = map(string)
  default     = {}
}
