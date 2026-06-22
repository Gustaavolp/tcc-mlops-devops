# -----------------------------------------------------------------------------
# Configuração do Terraform
# -----------------------------------------------------------------------------
# Terraform >= 1.11.0 necessário para S3 native locking (use_lockfile = true)
# Provider AWS ~> 6.0 para recursos mais recentes

terraform {
  required_version = "~> 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# -----------------------------------------------------------------------------
# Provider AWS
# -----------------------------------------------------------------------------
# Região centralizada para armazenamento de todos os Terraform states
# Tags padrão aplicadas automaticamente em todos os recursos

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# -----------------------------------------------------------------------------
# S3 Bucket para Terraform State
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket_name

  tags = {
    Name        = var.state_bucket_name
    Description = "Bucket para armazenar Terraform state files"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Habilitar versionamento (obrigatório para recuperação de state)
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}