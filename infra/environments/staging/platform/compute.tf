# ==============================================================================
# Compute Configuration - EKS Cluster
# ==============================================================================
# Este arquivo instancia o módulo EKS para criar o cluster Kubernetes.
# Arquitetura: Migração ECS → EKS mantendo compatibilidade com VPC Link + NLB.
# VPC vem da stack Foundation via remote_state.
# ==============================================================================

module "eks" {
  source = "../../../modules/eks"

  # Cluster Configuration
  cluster_name    = "${var.project_name}-cluster-${var.environment}"
  cluster_version = var.cluster_version # 1.32

  # Environment - necessário para criar node role com nome padrão elo-fraud-*
  environment = var.environment

  # Network Configuration (via remote_state da Foundation)
  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnet_ids

  # Node Group Configuration
  # t3.xlarge: 4 vCPU, 16GB RAM - otimizado para testes de latencia em staging
  node_instance_types = var.node_instance_types
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
  node_desired_size   = var.node_desired_size

  # Access Entries - Acesso admin via SSO para kubectl
  access_entries = var.eks_access_entries
}
