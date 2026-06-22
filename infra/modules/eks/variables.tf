# ==============================================================================
# EKS Module - Input Variables
# ==============================================================================
# Variables for configuring the EKS cluster and node groups.
# ==============================================================================

variable "cluster_name" {
  description = "Name of the EKS cluster. Should follow pattern: elo-fraud-cluster-{env}"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.cluster_name))
    error_message = "Cluster name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster. Must be a supported EKS version."
  type        = string
  default     = "1.32"

  validation {
    condition     = can(regex("^1\\.(2[7-9]|[3-9][0-9])$", var.cluster_version))
    error_message = "Cluster version must be 1.27 or higher."
  }
}

variable "vpc_id" {
  description = "ID of the VPC where the EKS cluster will be deployed."
  type        = string

  validation {
    condition     = can(regex("^vpc-", var.vpc_id))
    error_message = "VPC ID must start with 'vpc-'."
  }
}

variable "subnet_ids" {
  description = "List of subnet IDs where EKS nodes will be deployed. Should be private subnets across multiple AZs for HA."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least 2 subnet IDs are required for high availability."
  }
}

variable "node_instance_types" {
  description = "List of EC2 instance types for the managed node group. x86_64 instances for compatibility."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum number of nodes in the managed node group. Should be at least 2 for HA (1 allowed for dev)."
  type        = number
  default     = 2

  validation {
    condition     = var.node_min_size >= 1
    error_message = "Minimum node size must be at least 1 (production should use 2+ for HA)."
  }
}

variable "node_max_size" {
  description = "Maximum number of nodes in the managed node group. Used for auto-scaling."
  type        = number
  default     = 4

  validation {
    condition     = var.node_max_size >= var.node_min_size
    error_message = "Maximum node size must be greater than or equal to minimum node size."
  }
}

variable "node_desired_size" {
  description = "Desired number of nodes in the managed node group. Should be between min and max."
  type        = number
  default     = 2

  validation {
    condition     = var.node_desired_size >= 1
    error_message = "Desired node size must be at least 1 (production should use 2+ for HA)."
  }
}

variable "environment" {
  description = "Ambiente. Usado para nomear IAM roles."
  type        = string
  default     = "dev"
}

# -----------------------------------------------------------------------------
# EBS Volume Configuration
# -----------------------------------------------------------------------------

variable "ebs_volume_size" {
  description = "Tamanho do volume EBS em GB para nodes EKS"
  type        = number
  default     = 50
}

variable "ebs_volume_type" {
  description = "Tipo de volume EBS (gp3, gp2, io1, etc.)"
  type        = string
  default     = "gp3"
}

variable "ebs_iops" {
  description = "IOPS para volume EBS (apenas para gp3 e io1)"
  type        = number
  default     = 3000
}

variable "ebs_throughput" {
  description = "Throughput em MB/s para volume EBS (apenas para gp3)"
  type        = number
  default     = 125
}

# -----------------------------------------------------------------------------
# Node Configuration
# -----------------------------------------------------------------------------

variable "node_ami_type" {
  description = "Tipo de AMI para nodes EKS (AL2023_x86_64_STANDARD, AL2_x86_64, etc.)"
  type        = string
  default     = "AL2023_x86_64_STANDARD"
}

variable "update_max_unavailable_percentage" {
  description = "Percentual maximo de nodes indisponiveis durante updates"
  type        = number
  default     = 33
}

# -----------------------------------------------------------------------------
# Cluster Endpoint Access Configuration
# -----------------------------------------------------------------------------

variable "endpoint_public_access" {
  description = "Habilitar acesso publico ao endpoint do cluster (kubectl de fora da VPC)"
  type        = bool
  default     = true
}

variable "endpoint_private_access" {
  description = "Habilitar acesso privado ao endpoint do cluster (nodes na VPC)"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Cluster Admin Configuration
# -----------------------------------------------------------------------------

variable "enable_cluster_creator_admin_permissions" {
  description = "Permitir que o IAM principal que criou o cluster tenha acesso admin"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# Node Capacity Configuration
# -----------------------------------------------------------------------------

variable "capacity_type" {
  description = "Tipo de capacidade dos nodes (ON_DEMAND ou SPOT)"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.capacity_type)
    error_message = "capacity_type deve ser ON_DEMAND ou SPOT"
  }
}

# -----------------------------------------------------------------------------
# Node Labels Configuration
# -----------------------------------------------------------------------------

variable "node_labels" {
  description = "Labels para os nodes do cluster"
  type        = map(string)
  default = {
    role = "general"
  }
}

# -----------------------------------------------------------------------------
# EKS Access Entries Configuration
# -----------------------------------------------------------------------------

variable "access_entries" {
  description = "Map de access entries para controle de acesso ao cluster EKS via API (substitui aws-auth ConfigMap)"
  type = map(object({
    principal_arn     = string
    kubernetes_groups = optional(list(string), [])
    policy_associations = optional(map(object({
      policy_arn = string
      access_scope = object({
        type       = string
        namespaces = optional(list(string), [])
      })
    })), {})
  }))
  default = {}
}
