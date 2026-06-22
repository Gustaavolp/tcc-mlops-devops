# =============================================================================
# TERRAFORM VARIABLES - FOUNDATION DEV (us-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

# VPC
vpc_cidr = "10.0.0.0/16"

# Subnets (explicitas por AZ)
availability_zone_a   = "us-east-1a"
availability_zone_b   = "us-east-1b"
public_subnet_cidr_a  = "10.0.1.0/24"
public_subnet_cidr_b  = "10.0.2.0/24"
private_subnet_cidr_a = "10.0.11.0/24"
private_subnet_cidr_b = "10.0.12.0/24"

# VPC Options
enable_dns_hostnames           = true
enable_dns_support             = true
map_public_ip_on_launch        = true
interface_endpoint_private_dns = true

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Foundation"
  Region      = "us-east-1"
}
