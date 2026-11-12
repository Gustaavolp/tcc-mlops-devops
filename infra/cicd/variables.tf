variable "project_name" {
  description = "Prefixo dos recursos"
  type        = string
  default     = "elo-fraud"
}

variable "environments" {
  description = "Ambientes de implantação, na ordem de promoção (dev -> staging)"
  type = map(object({
    region = string
  }))
  default = {
    dev     = { region = "us-east-1" }
    staging = { region = "sa-east-1" }
  }

  validation {
    condition     = alltrue([for e in ["dev", "staging"] : contains(keys(var.environments), e)])
    error_message = "Os ambientes dev e staging são obrigatórios."
  }
}

variable "repository_name" {
  description = "Repositório AWS CodeCommit (monorepo) que dispara os pipelines"
  type        = string
  default     = "compra-online-repo"
}

variable "create_repository" {
  description = "Cria o repositório CodeCommit (false se ele já existir)"
  type        = bool
  default     = true
}

variable "branch" {
  description = "Branch cujos pushes disparam os pipelines"
  type        = string
  default     = "main"
}

variable "state_bucket" {
  description = "Bucket de estado do Terraform (leitura das saídas das stacks platform)"
  type        = string
  default     = "elo-fraud-terraform-state-888577064416-us-east-1"
}

variable "state_bucket_region" {
  description = "Região do bucket de estado"
  type        = string
  default     = "us-east-1"
}

variable "k8s_namespace" {
  description = "Namespace Kubernetes dos serviços"
  type        = string
  default     = "fraud-detection"
}

variable "codebuild_image" {
  description = "Imagem gerenciada do CodeBuild"
  type        = string
  default     = "aws/codebuild/standard:7.0"
}

variable "log_retention_days" {
  description = "Retenção dos logs do CodeBuild"
  type        = number
  default     = 30
}

variable "approval_sns_topic_arn" {
  description = "Tópico SNS opcional notificado nas aprovações manuais (null = sem notificação)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags adicionais"
  type        = map(string)
  default     = {}
}
