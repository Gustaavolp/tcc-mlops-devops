# ==============================================================================
# EKS Module - Outputs
# ==============================================================================
# Outputs for use by other modules and for cluster configuration.
# ==============================================================================

output "cluster_id" {
  description = "The ID of the EKS cluster. Used for resource identification and tagging."
  value       = module.eks.cluster_id
}

output "cluster_name" {
  description = "The name of the EKS cluster."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "The endpoint URL for the EKS Kubernetes API server. Used to configure kubectl."
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster. Used for kubectl configuration."
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_version" {
  description = "The Kubernetes version running on the EKS cluster."
  value       = module.eks.cluster_version
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for EKS. Required for IRSA (IAM Roles for Service Accounts) trust policies."
  value       = module.eks.oidc_provider_arn
}

output "oidc_provider_url" {
  description = "URL of the OIDC Provider for EKS without 'https://' prefix. Used in IRSA trust policy conditions."
  value       = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
}

output "node_security_group_id" {
  description = "Security group ID attached to the EKS worker nodes. Used for additional security rules."
  value       = module.eks.node_security_group_id
}

# ==============================================================================
# Node Group Outputs
# ==============================================================================

output "node_group_id" {
  description = "ID of the general purpose managed node group."
  value       = module.eks.eks_managed_node_groups["general"].node_group_id
}

output "node_group_status" {
  description = "Status of the general purpose managed node group."
  value       = module.eks.eks_managed_node_groups["general"].node_group_status
}
