# -----------------------------------------------------------------------------
# Lambda Module Outputs (Container Image Only)
# -----------------------------------------------------------------------------

output "function_name" {
  description = "Nome da função Lambda"
  value       = aws_lambda_function.container.function_name
}

output "function_arn" {
  description = "ARN da função Lambda"
  value       = aws_lambda_function.container.arn
}

output "role_arn" {
  description = "ARN da IAM Role"
  value       = aws_iam_role.lambda.arn
}
