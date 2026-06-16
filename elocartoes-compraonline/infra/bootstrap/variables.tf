# =============================================================================
# BOOTSTRAP VARIABLES - Terraform State Management (Centralizado)
# =============================================================================
# Este bootstrap é ÚNICO para todos os ambientes (dev, staging, prod).
# Os states são separados por prefixo no S3: dev/, staging/, prod/
# =============================================================================

variable "aws_region" {
  description = "Região AWS onde o state será armazenado (centralizado)"
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Nome do bucket S3 para Terraform state (obrigatório). Formato recomendado: {project}-terraform-state-{account}-{region}"
  type        = string
}

variable "tags" {
  description = "Tags comuns para todos os recursos"
  type        = map(string)
  default = {
    Project   = "Elo Fraud Detection"
    ManagedBy = "Terraform"
    Owner     = "DevOps"
    Purpose   = "Terraform State Management"
  }
}
