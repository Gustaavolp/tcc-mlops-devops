# =============================================================================
# PLATFORM-K8S BACKEND - STAGING (sa-east-1)
# =============================================================================
# Stack separada para recursos Kubernetes (Helm, ConfigMaps, TargetGroupBinding)
# Depende da stack platform (EKS, ALB, DynamoDB, SQS, etc.)
# =============================================================================

terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "staging/platform-k8s/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
