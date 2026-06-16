# =============================================================================
# VARIABLES - FOUNDATION STACK
# =============================================================================
# Este arquivo declara as variáveis da stack.
# Os valores são definidos em terraform.tfvars
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente"
  type        = string
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

# -----------------------------------------------------------------------------
# VPC Configuration
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block da VPC"
  type        = string
}

variable "availability_zone_a" {
  description = "Availability Zone A"
  type        = string
}

variable "availability_zone_b" {
  description = "Availability Zone B"
  type        = string
}

variable "public_subnet_cidr_a" {
  description = "CIDR da subnet publica na AZ A"
  type        = string
}

variable "public_subnet_cidr_b" {
  description = "CIDR da subnet publica na AZ B"
  type        = string
}

variable "private_subnet_cidr_a" {
  description = "CIDR da subnet privada na AZ A"
  type        = string
}

variable "private_subnet_cidr_b" {
  description = "CIDR da subnet privada na AZ B"
  type        = string
}

# -----------------------------------------------------------------------------
# VPC Options
# -----------------------------------------------------------------------------

variable "enable_dns_hostnames" {
  description = "Habilitar DNS hostnames na VPC (obrigatorio para EKS e VPC Endpoints)"
  type        = bool
}

variable "enable_dns_support" {
  description = "Habilitar DNS support na VPC (obrigatorio para resolucao DNS interna)"
  type        = bool
}

variable "map_public_ip_on_launch" {
  description = "Atribuir IP publico automaticamente para instancias em subnets publicas"
  type        = bool
}

variable "interface_endpoint_private_dns" {
  description = "Habilitar private DNS para VPC Interface Endpoints"
  type        = bool
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "common_tags" {
  description = "Tags comuns aplicadas a todos os recursos"
  type        = map(string)
}

