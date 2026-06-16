# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpc-${var.environment}"
    }
  )
}

# -----------------------------------------------------------------------------
# Internet Gateway
# -----------------------------------------------------------------------------

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-igw-${var.environment}"
    }
  )
}

# -----------------------------------------------------------------------------
# Public Subnets
# -----------------------------------------------------------------------------

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr_a
  availability_zone       = var.availability_zone_a
  map_public_ip_on_launch = var.map_public_ip_on_launch

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-public-subnet-${var.environment}-${var.availability_zone_a}"
      Type = "public"
    }
  )
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr_b
  availability_zone       = var.availability_zone_b
  map_public_ip_on_launch = var.map_public_ip_on_launch

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-public-subnet-${var.environment}-${var.availability_zone_b}"
      Type = "public"
    }
  )
}

# -----------------------------------------------------------------------------
# Private Subnets
# -----------------------------------------------------------------------------

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr_a
  availability_zone = var.availability_zone_a

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-private-subnet-${var.environment}-${var.availability_zone_a}"
      Type = "private"
    }
  )
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr_b
  availability_zone = var.availability_zone_b

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-private-subnet-${var.environment}-${var.availability_zone_b}"
      Type = "private"
    }
  )
}

# -----------------------------------------------------------------------------
# NAT Gateway
# -----------------------------------------------------------------------------

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-eip-nat-${var.environment}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-nat-${var.environment}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# -----------------------------------------------------------------------------
# Route Tables
# -----------------------------------------------------------------------------

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-rt-public-${var.environment}"
      Type = "public"
    }
  )
}

# Route para Internet Gateway
resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Associar subnets publicas a route table publica
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# Private Route Table (single NAT Gateway)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-rt-private-${var.environment}"
      Type = "private"
    }
  )
}

# Route para NAT Gateway
resource "aws_route" "private_nat_gateway" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}

# Associar subnets privadas a route table privada
resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

# -----------------------------------------------------------------------------
# VPC Gateway Endpoints (gratuitos)
# -----------------------------------------------------------------------------

# VPC Endpoint para S3 (Gateway)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.id}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id, aws_route_table.private.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-s3-${var.environment}"
      Type = "Gateway"
    }
  )
}

# VPC Endpoint para DynamoDB (Gateway)
resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.id}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id, aws_route_table.private.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-dynamodb-${var.environment}"
      Type = "Gateway"
    }
  )
}

# -----------------------------------------------------------------------------
# Security Group para VPC Interface Endpoints
# -----------------------------------------------------------------------------

resource "aws_security_group" "vpc_endpoints" {

  name_prefix = "${var.project_name}-vpc-endpoints-${var.environment}-"
  description = "Security group para VPC Interface Endpoints"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-sg-vpc-endpoints-${var.environment}"
      Purpose = "VPC Interface Endpoints"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# Ingress: HTTPS (443) de toda a VPC
resource "aws_vpc_security_group_ingress_rule" "vpc_endpoints_https" {

  security_group_id = aws_security_group.vpc_endpoints.id
  description       = "Allow HTTPS from VPC"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = var.vpc_cidr

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpc-endpoints-https-${var.environment}"
    }
  )
}

# -----------------------------------------------------------------------------
# VPC Interface Endpoints (custo: ~$7.20/mês por endpoint por AZ)
# Acesso privado direto a serviços AWS sem passar pelo NAT Gateway
# -----------------------------------------------------------------------------

# VPC Endpoint para ECR API (necessário para docker pull)
resource "aws_vpc_endpoint" "ecr_api" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-ecr-api-${var.environment}"
      Type = "Interface"
    }
  )
}

# VPC Endpoint para ECR DKR (Docker registry)
resource "aws_vpc_endpoint" "ecr_dkr" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-ecr-dkr-${var.environment}"
      Type = "Interface"
    }
  )
}

# VPC Endpoint para CloudWatch Logs
resource "aws_vpc_endpoint" "logs" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-logs-${var.environment}"
      Type = "Interface"
    }
  )
}

# VPC Endpoint para SQS
resource "aws_vpc_endpoint" "sqs" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.sqs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-vpce-sqs-${var.environment}"
      Type = "Interface"
    }
  )
}

# -----------------------------------------------------------------------------
# VPC Endpoints para EKS (otimizam custo e latencia para nodes em subnets privadas)
# -----------------------------------------------------------------------------

# VPC Endpoint para STS (OBRIGATÓRIO para EKS IAM authentication)
resource "aws_vpc_endpoint" "sts" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.sts"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-vpce-sts-${var.environment}"
      Type    = "Interface"
      Purpose = "EKS IAM Authentication"
    }
  )
}

# VPC Endpoint para EC2 (OBRIGATÓRIO para EKS VPC CNI plugin)
resource "aws_vpc_endpoint" "ec2" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.ec2"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-vpce-ec2-${var.environment}"
      Type    = "Interface"
      Purpose = "EKS VPC CNI"
    }
  )
}

# -----------------------------------------------------------------------------
# VPC Endpoints para SageMaker (utilizados pelo MLflow com backend SageMaker)
# -----------------------------------------------------------------------------

# VPC Endpoint para SageMaker API (registro e gerenciamento de modelos via MLflow)
resource "aws_vpc_endpoint" "sagemaker_api" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.sagemaker.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-vpce-sagemaker-api-${var.environment}"
      Type    = "Interface"
      Purpose = "SageMaker API"
    }
  )
}

# VPC Endpoint para SageMaker Runtime (nao utilizado atualmente - inferencia e local via MLflow)
resource "aws_vpc_endpoint" "sagemaker_runtime" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.sagemaker.runtime"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-vpce-sagemaker-runtime-${var.environment}"
      Type    = "Interface"
      Purpose = "SageMaker Inference"
    }
  )
}

# -----------------------------------------------------------------------------
# VPC Endpoint para Kinesis Firehose (necessário para streaming de dados)
# -----------------------------------------------------------------------------

resource "aws_vpc_endpoint" "firehose" {

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.id}.kinesis-firehose"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = var.interface_endpoint_private_dns
  subnet_ids          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  security_group_ids  = [aws_security_group.vpc_endpoints.id]

  tags = merge(
    var.tags,
    {
      Name    = "${var.project_name}-vpce-firehose-${var.environment}"
      Type    = "Interface"
      Purpose = "Kinesis Firehose"
    }
  )
}
