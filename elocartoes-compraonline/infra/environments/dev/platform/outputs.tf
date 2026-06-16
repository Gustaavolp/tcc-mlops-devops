# =============================================================================
# PLATFORM STACK OUTPUTS
# =============================================================================
# Outputs consumidos por stacks downstream via terraform_remote_state:
#   - platform-k8s: EKS cluster info + VPC ID
#   - platform-lambdas: ECR repository URLs
# =============================================================================

# -----------------------------------------------------------------------------
# EKS Outputs (consumidos por platform-k8s)
# -----------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "Nome do cluster EKS"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint do API server EKS"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "Certificado CA do cluster EKS (base64)"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

# -----------------------------------------------------------------------------
# VPC Output (consumido por platform-k8s)
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID da VPC (da Foundation)"
  value       = local.vpc_id
}

# -----------------------------------------------------------------------------
# ECR Outputs (consumidos por platform-lambdas)
# -----------------------------------------------------------------------------

output "ecr_model_repository_url" {
  description = "URL do repositorio ECR de model"
  value       = module.ecr.model_repository_url
}

output "ecr_register_best_model_url" {
  description = "URL do repositorio ECR para Lambda register-best-model"
  value       = module.ecr.best_model_register_repository_url
}

output "ecr_etl_delta_filter_url" {
  description = "URL do repositorio ECR para Lambda etl-delta-filter"
  value       = module.ecr.etl_delta_filter_repository_url
}

output "ecr_training_launcher_url" {
  description = "URL do repositorio ECR para Lambda training-launcher"
  value       = module.ecr.training_launcher_repository_url
}
