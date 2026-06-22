# =============================================================================
# Bootstrap - Terraform State Management (Centralizado)
# =============================================================================
# Este bootstrap e UNICO para todos os ambientes (dev, staging, prod).
# Os states sao separados por prefixo no S3: dev/, staging/, prod/
# =============================================================================

# Regiao AWS centralizada para todos os states
aws_region = "us-east-1"

# Nome do bucket S3
state_bucket_name = "elo-fraud-terraform-state-888577064416-us-east-1"

# Tags
tags = {
  Project   = "Elo Fraud Detection"
  ManagedBy = "Terraform"
  Owner     = "DevOps"
  Purpose   = "Terraform State Management"
}
