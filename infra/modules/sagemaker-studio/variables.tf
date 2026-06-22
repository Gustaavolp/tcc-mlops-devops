# -----------------------------------------------------------------------------
# SageMaker Studio Domain Variables
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Tags comuns para todos os recursos"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Resource Names (Explicit)
# -----------------------------------------------------------------------------

variable "domain_name" {
  description = "Nome do SageMaker Studio Domain"
  type        = string
}

variable "execution_role_name" {
  description = "Nome da IAM Execution Role para o Studio"
  type        = string
}

variable "log_group_name" {
  description = "Nome do CloudWatch Log Group"
  type        = string
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------
# NOTA: vpc_id e subnet_ids sao obrigatorios pela AWS, mesmo em PublicInternetOnly.
# O SageMaker cria recursos na VPC (EFS para home directories).
# -----------------------------------------------------------------------------

variable "vpc_id" {
  description = "ID da VPC para o SageMaker Studio Domain"
  type        = string

  validation {
    condition     = can(regex("^vpc-[a-z0-9]+$", var.vpc_id))
    error_message = "vpc_id deve ser um VPC ID valido (ex: vpc-abc123)"
  }
}

variable "subnet_ids" {
  description = "IDs das subnets para o SageMaker Studio Domain (minimo 1)"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 1
    error_message = "Pelo menos 1 subnet e necessaria"
  }
}

variable "vpc_cidr" {
  description = "CIDR block da VPC (necessario para regras do Security Group no modo VpcOnly)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Default Instance Types
# -----------------------------------------------------------------------------

variable "default_notebook_instance_type" {
  description = "Instance type padrão para notebooks (KernelGateway)"
  type        = string
  default     = "ml.t3.medium"

  validation {
    condition     = can(regex("^ml\\.[a-z0-9]+\\.[a-z]+$", var.default_notebook_instance_type))
    error_message = "default_notebook_instance_type deve ser um instance type SageMaker válido (ex: ml.t3.medium)"
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
    error_message = "log_retention_days deve ser um valor válido do CloudWatch"
  }
}

# -----------------------------------------------------------------------------
# Idle Shutdown Configuration (Auto-Stop Apps Ociosos)
# -----------------------------------------------------------------------------

variable "idle_timeout_in_minutes" {
  description = "Tempo de ociosidade antes de desligar o app (minutos, minimo 60)"
  type        = number
}

# -----------------------------------------------------------------------------
# User Profiles Configuration
# -----------------------------------------------------------------------------

variable "user_profiles" {
  description = "Lista de User Profiles a serem criados. Cada item: {name, execution_role_arn (opcional)}"
  type = list(object({
    name               = string
    execution_role_arn = optional(string, null)
  }))
  default = []
}

# -----------------------------------------------------------------------------
# Network Access Configuration
# -----------------------------------------------------------------------------

variable "app_network_access_type" {
  description = "Tipo de acesso de rede para apps (PublicInternetOnly ou VpcOnly)"
  type        = string
  default     = "PublicInternetOnly"

  validation {
    condition     = contains(["PublicInternetOnly", "VpcOnly"], var.app_network_access_type)
    error_message = "app_network_access_type deve ser PublicInternetOnly ou VpcOnly"
  }
}

# -----------------------------------------------------------------------------
# App Lifecycle Management Configuration
# -----------------------------------------------------------------------------

variable "lifecycle_management_enabled" {
  description = "Habilitar gerenciamento de lifecycle para apps ociosos (ENABLED ou DISABLED)"
  type        = string
  default     = "ENABLED"

  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.lifecycle_management_enabled)
    error_message = "lifecycle_management_enabled deve ser ENABLED ou DISABLED"
  }
}

variable "notebook_output_option" {
  description = "Opcao de output de notebooks (Allowed ou Disabled)"
  type        = string
  default     = "Allowed"

  validation {
    condition     = contains(["Allowed", "Disabled"], var.notebook_output_option)
    error_message = "notebook_output_option deve ser Allowed ou Disabled"
  }
}
