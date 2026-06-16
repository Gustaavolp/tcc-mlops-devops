# =============================================================================
# VARIABLES - PLATFORM K8S STACK
# =============================================================================
# Este arquivo declara as variaveis da stack.
# Os valores sao definidos em terraform.tfvars
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Ambiente"
  type        = string
}

variable "aws_region" {
  description = "Regiao AWS"
  type        = string
}

