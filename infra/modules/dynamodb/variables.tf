# -----------------------------------------------------------------------------
# Variáveis Básicas
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Configuração da Tabela
# -----------------------------------------------------------------------------

variable "table_name_suffix" {
  description = "Sufixo do nome da tabela (ex: customer-recent-tx)"
  type        = string
  default     = "customer-recent-tx"
}

variable "hash_key" {
  description = "Nome do partition key (hash key)"
  type        = string
  default     = "acctID"
}

variable "hash_key_type" {
  description = "Tipo do partition key (S = String, N = Number, B = Binary)"
  type        = string
  default     = "S"

  validation {
    condition     = contains(["S", "N", "B"], var.hash_key_type)
    error_message = "O tipo deve ser S (String), N (Number) ou B (Binary)."
  }
}

variable "range_key" {
  description = "Nome do sort key (range key)"
  type        = string
  default     = "threeDSServerTransID"
}

variable "range_key_type" {
  description = "Tipo do sort key (S = String, N = Number, B = Binary)"
  type        = string
  default     = "S"

  validation {
    condition     = contains(["S", "N", "B"], var.range_key_type)
    error_message = "O tipo deve ser S (String), N (Number) ou B (Binary)."
  }
}

# -----------------------------------------------------------------------------
# Segurança e Resiliência
# -----------------------------------------------------------------------------

variable "point_in_time_recovery_enabled" {
  description = "Habilitar Point-in-Time Recovery para backup contínuo"
  type        = bool
  default     = false
}

variable "deletion_protection_enabled" {
  description = "Proteger tabela contra deleção acidental"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Billing Configuration
# -----------------------------------------------------------------------------

variable "billing_mode" {
  description = "Modo de cobranca do DynamoDB (PAY_PER_REQUEST ou PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.billing_mode)
    error_message = "billing_mode deve ser PAY_PER_REQUEST ou PROVISIONED"
  }
}
