# =============================================================================
# BACKEND CONFIGURATION - FOUNDATION DEV
# =============================================================================

terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "dev/foundation/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
