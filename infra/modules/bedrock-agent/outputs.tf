# -----------------------------------------------------------------------------
# Bedrock Agent Module - Outputs
# -----------------------------------------------------------------------------

output "role_arn" {
  description = "ARN da Bedrock Agent Role"
  value       = aws_iam_role.bedrock_agent.arn
}

output "role_name" {
  description = "Nome da Bedrock Agent Role"
  value       = aws_iam_role.bedrock_agent.name
}
