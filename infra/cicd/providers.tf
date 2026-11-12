# Região principal (DEV e todos os pipelines)
provider "aws" {
  region = var.environments["dev"].region

  default_tags {
    tags = local.tags
  }
}

# Região de Staging: projeto de rollout do modelo, regra do EventBridge e acesso ao EKS
provider "aws" {
  alias  = "staging"
  region = var.environments["staging"].region

  default_tags {
    tags = local.tags
  }
}
