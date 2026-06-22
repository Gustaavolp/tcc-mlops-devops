# =============================================================================
# BACKEND CONFIGURATION - PLATFORM STAGING
# =============================================================================

terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "staging/platform/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
