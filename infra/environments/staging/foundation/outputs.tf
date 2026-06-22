# =============================================================================
# FOUNDATION OUTPUTS
# =============================================================================
# Estes outputs são usados pelas stacks MLOps e Platform via remote_state
# =============================================================================

# -----------------------------------------------------------------------------
# VPC Outputs
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "ID da VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR da VPC"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "IDs das subnets públicas"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = module.vpc.private_subnet_ids
}

# -----------------------------------------------------------------------------
# S3 Outputs
# -----------------------------------------------------------------------------
output "s3_processed_bucket_id" {
  description = "ID do bucket processed"
  value       = module.s3.processed_bucket_id
}

output "s3_processed_bucket_arn" {
  description = "ARN do bucket processed"
  value       = module.s3.processed_bucket_arn
}
