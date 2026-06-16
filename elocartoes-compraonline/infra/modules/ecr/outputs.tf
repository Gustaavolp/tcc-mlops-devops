# -----------------------------------------------------------------------------
# ECR Outputs
# -----------------------------------------------------------------------------

# Inference Repository
output "inference_repository_url" {
  description = "URL do repositório ECR de inference"
  value       = aws_ecr_repository.inference.repository_url
}

output "inference_repository_arn" {
  description = "ARN do repositório ECR de inference"
  value       = aws_ecr_repository.inference.arn
}

# Process Repository
output "process_repository_url" {
  description = "URL do repositório ECR de process"
  value       = aws_ecr_repository.process.repository_url
}

output "process_repository_arn" {
  description = "ARN do repositório ECR de process"
  value       = aws_ecr_repository.process.arn
}

# Model Repository
output "model_repository_url" {
  description = "URL do repositório ECR de model"
  value       = aws_ecr_repository.model.repository_url
}

output "model_repository_arn" {
  description = "ARN do repositório ECR de model"
  value       = aws_ecr_repository.model.arn
}

# Best Model Register Repository (Lambda)
output "best_model_register_repository_url" {
  description = "URL do repositório ECR best-model-register"
  value       = aws_ecr_repository.best_model_register.repository_url
}

output "best_model_register_repository_arn" {
  description = "ARN do repositório ECR best-model-register"
  value       = aws_ecr_repository.best_model_register.arn
}

# ETL Delta Filter Repository (Lambda)
output "etl_delta_filter_repository_url" {
  description = "URL do repositório ECR etl-delta-filter"
  value       = aws_ecr_repository.etl_delta_filter.repository_url
}

output "etl_delta_filter_repository_arn" {
  description = "ARN do repositório ECR etl-delta-filter"
  value       = aws_ecr_repository.etl_delta_filter.arn
}

# Training Launcher Repository (Lambda)
output "training_launcher_repository_url" {
  description = "URL do repositório ECR training-launcher"
  value       = aws_ecr_repository.training_launcher.repository_url
}

output "training_launcher_repository_arn" {
  description = "ARN do repositório ECR training-launcher"
  value       = aws_ecr_repository.training_launcher.arn
}
