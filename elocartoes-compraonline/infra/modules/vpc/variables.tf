variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prd)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block da VPC"
  type        = string

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR deve ser um CIDR válido."
  }
}

variable "availability_zone_a" {
  description = "Availability Zone A (ex: us-east-1a, sa-east-1a)"
  type        = string
}

variable "availability_zone_b" {
  description = "Availability Zone B (ex: us-east-1b, sa-east-1b)"
  type        = string
}

variable "public_subnet_cidr_a" {
  description = "CIDR da subnet publica na AZ A"
  type        = string

  validation {
    condition     = can(cidrhost(var.public_subnet_cidr_a, 0))
    error_message = "public_subnet_cidr_a deve ser um CIDR valido."
  }
}

variable "public_subnet_cidr_b" {
  description = "CIDR da subnet publica na AZ B"
  type        = string

  validation {
    condition     = can(cidrhost(var.public_subnet_cidr_b, 0))
    error_message = "public_subnet_cidr_b deve ser um CIDR valido."
  }
}

variable "private_subnet_cidr_a" {
  description = "CIDR da subnet privada na AZ A"
  type        = string

  validation {
    condition     = can(cidrhost(var.private_subnet_cidr_a, 0))
    error_message = "private_subnet_cidr_a deve ser um CIDR valido."
  }
}

variable "private_subnet_cidr_b" {
  description = "CIDR da subnet privada na AZ B"
  type        = string

  validation {
    condition     = can(cidrhost(var.private_subnet_cidr_b, 0))
    error_message = "private_subnet_cidr_b deve ser um CIDR valido."
  }
}

variable "enable_dns_hostnames" {
  description = "Habilitar DNS hostnames na VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Habilitar DNS support na VPC"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags comuns para todos os recursos"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Public Subnet Configuration
# -----------------------------------------------------------------------------

variable "map_public_ip_on_launch" {
  description = "Atribuir IP publico automaticamente para instancias em subnets publicas"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# VPC Endpoint Configuration
# -----------------------------------------------------------------------------

variable "interface_endpoint_private_dns" {
  description = "Habilitar private DNS para VPC Interface Endpoints"
  type        = bool
  default     = true
}
