# =============================================================================
# FOUNDATION STACK
# =============================================================================
# Esta stack contém a infraestrutura base compartilhada:
# - VPC e Networking
# - S3 Buckets
# =============================================================================

# -----------------------------------------------------------------------------
# VPC Module
# -----------------------------------------------------------------------------
module "vpc" {
  source = "../../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr

  availability_zone_a   = var.availability_zone_a
  availability_zone_b   = var.availability_zone_b
  public_subnet_cidr_a  = var.public_subnet_cidr_a
  public_subnet_cidr_b  = var.public_subnet_cidr_b
  private_subnet_cidr_a = var.private_subnet_cidr_a
  private_subnet_cidr_b = var.private_subnet_cidr_b

  enable_dns_hostnames           = var.enable_dns_hostnames
  enable_dns_support             = var.enable_dns_support
  map_public_ip_on_launch        = var.map_public_ip_on_launch
  interface_endpoint_private_dns = var.interface_endpoint_private_dns

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# S3 Module
# -----------------------------------------------------------------------------
module "s3" {
  source = "../../../modules/s3"

  environment = var.environment

  # Nomes dos buckets (Data Lake)
  raw_bucket_name       = "${var.project_name}-data-raw-${var.environment}-${var.aws_account_id}"
  processed_bucket_name = "${var.project_name}-data-processed-${var.environment}-${var.aws_account_id}"
  models_bucket_name    = "${var.project_name}-models-${var.environment}-${var.aws_account_id}"
  logs_bucket_name      = "${var.project_name}-logs-${var.environment}-${var.aws_account_id}"

  # Nomes dos buckets (Utilitários)
  resources_bucket_name          = "${var.project_name}-resources-${var.environment}-${var.aws_account_id}"
  reports_promotion_bucket_name  = "${var.project_name}-reports-promotion-${var.environment}-${var.aws_account_id}"
  reports_statistics_bucket_name = "${var.project_name}-reports-statistics-${var.environment}-${var.aws_account_id}"

  tags = var.common_tags
}
