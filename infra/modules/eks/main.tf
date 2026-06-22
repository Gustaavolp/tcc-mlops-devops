# ==============================================================================
# EKS Cluster - Fraud Detection System
# ==============================================================================
# This module creates an Amazon EKS cluster for migrating from ECS to EKS.
# Architecture: Single node group (t3.medium x86_64) for compatibility.
# ==============================================================================

terraform {
  required_version = "~> 1.14.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# ==============================================================================
# EKS Cluster
# ==============================================================================
# Creates the EKS control plane with managed node groups.
# IRSA (IAM Roles for Service Accounts) enabled via OIDC provider.
# ==============================================================================

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  # Cluster Configuration
  name               = var.cluster_name
  kubernetes_version = var.cluster_version

  # Networking
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # ==============================================================================
  # IAM Role Configuration (SCP Workaround)
  # ==============================================================================
  # NOTA: A conta AWS tem SCP que bloqueia iam:TagRole e iam:CreatePolicy.
  # Configuramos para usar apenas AWS managed policies e evitar criação de custom policies.
  # ==============================================================================
  iam_role_tags = {}

  # ==============================================================================
  # KMS Encryption Configuration (SCP Workaround)
  # ==============================================================================
  # NOTA: EKS 21.x cria KMS key + IAM policy por padrão para encryption.
  # SCP bloqueia iam:CreatePolicy, então desabilitamos a criação de KMS key customizada.
  # Secrets ainda serão criptografados com AWS managed key (não requer IAM policy).
  # ==============================================================================
  create_kms_key    = false
  encryption_config = null # Usa AWS managed key em vez de custom KMS key

  # Cluster Endpoint Access
  # Public access enabled for kubectl from local/CI/CD (with authentication)
  # Private access enabled for nodes in VPC
  endpoint_public_access  = var.endpoint_public_access
  endpoint_private_access = var.endpoint_private_access

  # Enable cluster creator admin permissions
  # This allows the IAM principal that created the cluster to have admin access
  enable_cluster_creator_admin_permissions = var.enable_cluster_creator_admin_permissions

  # ==============================================================================
  # Access Entries - Controle de acesso ao cluster via EKS Access API
  # ==============================================================================
  # Substitui o aws-auth ConfigMap. Permite adicionar IAM principals (roles/users)
  # com policies de acesso ao cluster (ex: AmazonEKSClusterAdminPolicy).
  # ==============================================================================
  access_entries = var.access_entries

  # Control Plane Logging
  # DESABILITADO: SCP bloqueia iam:CreatePolicy necessário para CloudWatch
  # Para habilitar: ajustar SCP e adicionar ["api", "audit"]
  enabled_log_types           = []
  create_cloudwatch_log_group = false

  # Cluster Addons
  # Default configurations for CoreDNS, kube-proxy, VPC CNI, and Pod Identity Agent
  #
  # IMPORTANTE sobre before_compute:
  # - vpc-cni e kube-proxy: before_compute = true (nodes precisam deles para entrar no cluster)
  # - coredns: before_compute = false (é um Deployment que precisa de nodes para rodar)
  #
  # Se coredns tiver before_compute = true, ele fica DEGRADED esperando nodes que ainda não existem.
  addons = {
    coredns = {
      most_recent    = true
      before_compute = false # Criar DEPOIS dos nodes (coredns precisa de nodes para agendar pods)
    }
    kube-proxy = {
      most_recent    = true
      before_compute = true # Criar ANTES dos nodes (nodes precisam do kube-proxy)
    }
    vpc-cni = {
      most_recent    = true
      before_compute = true # Criar ANTES dos nodes (nodes precisam do CNI para obter IPs)
    }
    # ==========================================================================
    # EKS Pod Identity Agent
    # ==========================================================================
    # Instala DaemonSet que fornece credenciais IAM individuais por pod via
    # Pod Identity Associations (substitui IMDS/Node Role para pods).
    # NÃO requer OIDC provider (compatível com SCP que bloqueia CreateOpenIDConnectProvider).
    # Pods sem associação não são afetados — continuam usando IMDS enquanto hop_limit=2.
    # ==========================================================================
    eks-pod-identity-agent = {
      most_recent    = true
      before_compute = true # Agent precisa estar nos nodes antes dos pods de aplicação
    }
    # aws-ebs-csi-driver = {
    #   most_recent = true
    #   before_compute = true
    # }
    # TEMPORARIAMENTE COMENTADO: O EBS CSI Driver requer IAM Role com IRSA.
    # Será criado manualmente com: eks create-addon --service-account-role-arn
  }

  # ==============================================================================
  # Managed Node Group - General Purpose
  # ==============================================================================
  # Single node group for both inference and process workloads.
  # x86_64 (Intel) for compatibility.
  # ==============================================================================

  eks_managed_node_groups = {
    general = {
      name = "general"

      # ==============================================================================
      # IAM Role Configuration
      # ==============================================================================
      # Nome customizado seguindo padrão elo-fraud-* para compatibilidade com
      # políticas de CI/CD do CodeBuild que só permite modificar roles elo-fraud-*
      # ==============================================================================
      iam_role_name            = "elo-fraud-eks-node-role-${var.environment}"
      iam_role_use_name_prefix = false

      # Policies adicionais além das automáticas do módulo EKS
      # (AmazonEKSWorkerNodePolicy, AmazonEC2ContainerRegistryReadOnly, AmazonEKS_CNI_Policy)
      #
      # Policies de aplicacao (DynamoDB, SQS, S3, Firehose, ELB, SageMaker, EC2, AutoScaling)
      # foram REMOVIDAS — agora gerenciadas por Pod Identity com least-privilege por workload.
      # Ver pod-identity.tf na stack platform de cada ambiente.
      iam_role_additional_policies = {
        CloudWatchFullAccess        = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
        AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      }

      # Instance Configuration
      instance_types = var.node_instance_types
      capacity_type  = var.capacity_type # ON_DEMAND para latencia previsivel, SPOT para economia
      ami_type       = var.node_ami_type # Amazon Linux 2023 (migrated from AL2 on 2025-11-11)

      # Scaling Configuration
      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      # Disk Configuration (valores definidos via variaveis)
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = var.ebs_volume_size
            volume_type           = var.ebs_volume_type
            iops                  = var.ebs_iops
            throughput            = var.ebs_throughput
            encrypted             = true
            delete_on_termination = true
          }
        }
      }

      # Node Labels
      # Used for pod scheduling and node affinity rules
      labels = var.node_labels

      # Taints
      # No taints - all pods can schedule on these nodes
      taints = {}

      # Metadata Options (IMDS)
      # hop_limit=1: apenas o node acessa IMDS (pods usam Pod Identity para credenciais)
      # DaemonSets com hostNetwork=true (vpc-cni, kube-proxy, pod-identity-agent) continuam no hop 1
      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required" # IMDSv2 obrigatorio
        http_put_response_hop_limit = 1          # Bloqueia pods de acessarem IMDS
      }

      # Update Configuration (valor definido via variavel)
      # Rolling update strategy for zero-downtime deployments
      update_config = {
        max_unavailable_percentage = var.update_max_unavailable_percentage
      }

      # NOTA: Tags comentadas devido a SCP que bloqueia iam:TagRole
      # O módulo externo aplica tags aos IAM roles internamente
      iam_role_tags = {}
      tags          = {}
      # tags = merge(
      #   var.tags,
      #   {
      #     "k8s.io/cluster-autoscaler/enabled"             = "true"
      #     "k8s.io/cluster-autoscaler/${var.cluster_name}" = "owned"
      #   }
      # )
    }
  }

  # ==============================================================================
  # IAM Role for Service Accounts (IRSA)
  # ==============================================================================
  # DESABILITADO: SCP bloqueia iam:CreateOpenIDConnectProvider
  # Pods usarão IAM role do node em vez de IRSA.
  # Para habilitar: ajustar SCP e setar enable_irsa = true
  # ==============================================================================

  enable_irsa = false

  # ==============================================================================
  # Cluster Security Group
  # ==============================================================================
  # Allow communication between control plane and worker nodes.
  # ==============================================================================

  security_group_additional_rules = {
    ingress_nodes_ephemeral_ports_tcp = {
      description                = "Nodes on ephemeral ports"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "ingress"
      source_node_security_group = true
    }
  }

  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
    egress_all = {
      description      = "Node all egress"
      protocol         = "-1"
      from_port        = 0
      to_port          = 0
      type             = "egress"
      cidr_blocks      = ["0.0.0.0/0"]
      ipv6_cidr_blocks = ["::/0"]
    }
  }

  # NOTA: Tags comentadas devido a SCP que bloqueia iam:TagRole
  # O módulo aplica tags aos IAM roles internamente, causando erro
  tags = {}
  # tags = merge(
  #   var.tags,
  #   {
  #     Name      = var.cluster_name
  #     Component = "eks"
  #     ManagedBy = "terraform"
  #   }
  # )
}

# ==============================================================================
# OIDC Provider for IRSA
# ==============================================================================
# Automatically created by the EKS module.
# URL format: https://oidc.eks.{region}.amazonaws.com/id/{cluster-id}
# ==============================================================================
# No additional configuration needed - handled by module.eks

# ==============================================================================
# Inline policies de aplicacao REMOVIDAS (agora via Pod Identity)
# ==============================================================================
# As seguintes inline policies foram removidas do Node Role:
#   - SageMakerMLflowFullAccess  → inference Pod Identity role
#   - EC2FullAccess              → lb-controller Pod Identity role
#   - AutoScalingFullAccess      → autoscaler Pod Identity role
# Ver pod-identity.tf na stack platform de cada ambiente.
# ==============================================================================
