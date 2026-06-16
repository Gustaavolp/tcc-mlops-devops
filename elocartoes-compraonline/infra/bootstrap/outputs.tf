output "terraform_state_bucket_name" {
  description = "Nome do bucket S3 para Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_state_bucket_arn" {
  description = "ARN do bucket S3 para Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "terraform_state_bucket_region" {
  description = "Região do bucket S3"
  value       = aws_s3_bucket.terraform_state.region
}