# -----------------------------------------------------------------------------
# Glue Module - Outputs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IAM Role
# -----------------------------------------------------------------------------

output "role_arn" {
  description = "ARN da IAM Role para Glue Jobs"
  value       = aws_iam_role.glue.arn
}

output "role_name" {
  description = "Nome da IAM Role para Glue Jobs"
  value       = aws_iam_role.glue.name
}
