variable "environment" {
  description = "Ambiente (dev, stg, prd)"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# Repository Configuration
variable "enable_image_scanning" {
  description = "Habilitar scan automático de vulnerabilidades"
  type        = bool
  default     = true
}

variable "image_tag_mutability" {
  description = "Permitir sobrescrever tags de imagem (MUTABLE, IMMUTABLE ou *_WITH_EXCLUSION)"
  type        = string
  default     = "MUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE", "MUTABLE_WITH_EXCLUSION", "IMMUTABLE_WITH_EXCLUSION"], var.image_tag_mutability)
    error_message = "image_tag_mutability deve ser MUTABLE, IMMUTABLE, MUTABLE_WITH_EXCLUSION ou IMMUTABLE_WITH_EXCLUSION"
  }
}

variable "image_tag_mutability_exclusion_filters" {
  description = "Filtros (wildcard) de tags que escapam da regra de mutabilidade; usado com *_WITH_EXCLUSION (máx. 5)"
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.image_tag_mutability_exclusion_filters) <= 5
    error_message = "No máximo 5 filtros de exclusão."
  }
}

# Lifecycle Policies
variable "max_image_count" {
  description = "Número máximo de imagens a manter"
  type        = number
  default     = 30
}

variable "untagged_image_retention_days" {
  description = "Dias para manter imagens sem tag"
  type        = number
  default     = 7
}

# -----------------------------------------------------------------------------
# Repository Names
# -----------------------------------------------------------------------------
# Todos os repositórios são criados automaticamente.
# Os nomes devem ser fornecidos explicitamente.
# -----------------------------------------------------------------------------

variable "inference_repo_name" {
  description = "Nome do repositório ECR para serviço de inference"
  type        = string
}

variable "process_repo_name" {
  description = "Nome do repositório ECR para serviço de process"
  type        = string
}

variable "model_repo_name" {
  description = "Nome do repositório ECR para container de modelo ML"
  type        = string
}

variable "best_model_register_repo_name" {
  description = "Nome do repositório ECR para Lambda best-model-register"
  type        = string
}

variable "etl_delta_filter_repo_name" {
  description = "Nome do repositório ECR para Lambda etl-delta-filter"
  type        = string
}

variable "training_launcher_repo_name" {
  description = "Nome do repositório ECR para Lambda training-launcher"
  type        = string
}
