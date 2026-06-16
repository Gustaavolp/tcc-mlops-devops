# -----------------------------------------------------------------------------
# SageMaker Studio Domain Outputs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Domain
# -----------------------------------------------------------------------------

output "domain_id" {
  description = "ID do SageMaker Studio Domain"
  value       = aws_sagemaker_domain.main.id
}

output "domain_url" {
  description = "URL base do SageMaker Studio"
  value       = aws_sagemaker_domain.main.url
}

# -----------------------------------------------------------------------------
# IAM
# -----------------------------------------------------------------------------

output "execution_role_arn" {
  description = "ARN da IAM Execution Role (use em user profiles, notebooks, etc.)"
  value       = aws_iam_role.execution.arn
}

# -----------------------------------------------------------------------------
# Security Group (VpcOnly)
# -----------------------------------------------------------------------------

output "security_group_id" {
  description = "ID do Security Group do Studio (null se PublicInternetOnly)"
  value       = try(aws_security_group.studio[0].id, null)
}
