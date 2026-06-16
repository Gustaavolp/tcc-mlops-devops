# -----------------------------------------------------------------------------
# Bedrock Agent Module - Variables
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
  description = "Tags para os recursos"
  type        = map(string)
  default     = {}
}
