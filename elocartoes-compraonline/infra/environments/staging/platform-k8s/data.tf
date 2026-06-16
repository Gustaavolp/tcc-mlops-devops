# =============================================================================
# DATA SOURCES - Le outputs da stack Platform
# =============================================================================
# Esta stack depende da stack Platform para obter informacoes do EKS
# necessarias para configurar os providers Kubernetes/Helm e os addons.
# =============================================================================

# -----------------------------------------------------------------------------
# Remote State: Platform
# -----------------------------------------------------------------------------

data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "staging/platform/terraform.tfstate"
    region = "us-east-1"
  }
}

# -----------------------------------------------------------------------------
# Locals - Valores da stack Platform
# -----------------------------------------------------------------------------

locals {
  # EKS (usados pelos providers e Helm charts)
  eks_cluster_name                       = data.terraform_remote_state.platform.outputs.eks_cluster_name
  eks_cluster_endpoint                   = data.terraform_remote_state.platform.outputs.eks_cluster_endpoint
  eks_cluster_certificate_authority_data = data.terraform_remote_state.platform.outputs.eks_cluster_certificate_authority_data

  # VPC (usado pelo AWS Load Balancer Controller)
  vpc_id = data.terraform_remote_state.platform.outputs.vpc_id
}
