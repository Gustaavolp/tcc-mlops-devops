# =============================================================================
# BACKEND CONFIGURATION - PLATFORM LAMBDAS STAGING
# =============================================================================
# Stack separada para Lambdas container-based que dependem de imagens no ECR.
# Resolve o problema de dependencia circular: ECR vazio -> Lambda falha.
# =============================================================================

terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "staging/platform-lambdas/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
