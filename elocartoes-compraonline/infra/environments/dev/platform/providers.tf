# -----------------------------------------------------------------------------
# Terraform & Provider Configuration
# -----------------------------------------------------------------------------
# Este arquivo contém a configuração do Terraform e provider AWS.
#
# NOTA: Providers Kubernetes e Helm foram movidos para stack platform-k8s
# para resolver problema de dependência circular (2026-01-18).
# -----------------------------------------------------------------------------

terraform {
  required_version = "~> 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # NOTA: default_tags comentadas devido a SCP que bloqueia iam:TagRole
  # Quando o SCP for ajustado, descomentar para aplicar tags automaticamente
  # default_tags {
  #   tags = var.common_tags
  # }
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}
