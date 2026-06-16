# =============================================================================
# DATA SOURCES - Lê outputs da stack Foundation
# =============================================================================

data "aws_caller_identity" "current" {}

data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

locals {
  # AWS Account ID
  aws_account_id = data.aws_caller_identity.current.account_id

  # Valores da Foundation
  vpc_id            = data.terraform_remote_state.foundation.outputs.vpc_id
  public_subnet_ids = data.terraform_remote_state.foundation.outputs.public_subnet_ids

}
