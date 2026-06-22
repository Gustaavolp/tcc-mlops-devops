# =============================================================================
# PROVIDERS - PLATFORM LAMBDAS STAGING (sa-east-1)
# =============================================================================

terraform {
  required_version = "~> 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Stack       = "Platform-Lambdas"
      Region      = var.aws_region
    }
  }
}
