# =============================================================================
# DATA SOURCES - Lê outputs das stacks Foundation e MLOps
# =============================================================================

# -----------------------------------------------------------------------------
# Remote State: Foundation
# -----------------------------------------------------------------------------

data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "staging/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}
# -----------------------------------------------------------------------------
# Locals - Valores da stack Foundation
# -----------------------------------------------------------------------------

locals {
  # VPC
  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids

  # S3 Buckets
  s3_processed_bucket_arn = data.terraform_remote_state.foundation.outputs.s3_processed_bucket_arn
  s3_processed_bucket_id  = data.terraform_remote_state.foundation.outputs.s3_processed_bucket_id

  # NLB DNS (do modulo NLB Terraform)
  # Usado para integracao com VPC Link do API Gateway
  nlb_dns_name = module.nlb.nlb_dns_name
  nlb_arn      = module.nlb.nlb_arn
}
