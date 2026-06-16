# -----------------------------------------------------------------------------
# VPC Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID da VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block da VPC"
  value       = aws_vpc.main.cidr_block
}

# -----------------------------------------------------------------------------
# Subnet Outputs
# -----------------------------------------------------------------------------

output "public_subnet_ids" {
  description = "IDs das subnets publicas"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas"
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

# -----------------------------------------------------------------------------
# Gateway Outputs
# -----------------------------------------------------------------------------

output "internet_gateway_id" {
  description = "ID do Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_id" {
  description = "ID do NAT Gateway"
  value       = aws_nat_gateway.main.id
}

output "nat_gateway_public_ip" {
  description = "IP publico do NAT Gateway"
  value       = aws_eip.nat.public_ip
}

# -----------------------------------------------------------------------------
# VPC Endpoint Outputs
# -----------------------------------------------------------------------------

output "vpc_endpoint_ecr_api_id" {
  description = "ID do VPC Endpoint ECR API (Interface)"
  value       = aws_vpc_endpoint.ecr_api.id
}

output "vpc_endpoint_ecr_dkr_id" {
  description = "ID do VPC Endpoint ECR DKR (Interface)"
  value       = aws_vpc_endpoint.ecr_dkr.id
}

output "vpc_endpoint_logs_id" {
  description = "ID do VPC Endpoint CloudWatch Logs (Interface)"
  value       = aws_vpc_endpoint.logs.id
}

output "vpc_endpoint_sqs_id" {
  description = "ID do VPC Endpoint SQS (Interface)"
  value       = aws_vpc_endpoint.sqs.id
}

output "vpc_endpoint_sts_id" {
  description = "ID do VPC Endpoint STS (Interface - obrigatório para EKS)"
  value       = aws_vpc_endpoint.sts.id
}

output "vpc_endpoint_ec2_id" {
  description = "ID do VPC Endpoint EC2 (Interface - obrigatório para EKS VPC CNI)"
  value       = aws_vpc_endpoint.ec2.id
}

output "vpc_endpoint_sagemaker_api_id" {
  description = "ID do VPC Endpoint SageMaker API (Interface)"
  value       = aws_vpc_endpoint.sagemaker_api.id
}

output "vpc_endpoint_sagemaker_runtime_id" {
  description = "ID do VPC Endpoint SageMaker Runtime (Interface)"
  value       = aws_vpc_endpoint.sagemaker_runtime.id
}

output "vpc_endpoint_firehose_id" {
  description = "ID do VPC Endpoint Kinesis Firehose (Interface)"
  value       = aws_vpc_endpoint.firehose.id
}

output "security_group_vpc_endpoints_id" {
  description = "ID do Security Group dos VPC Interface Endpoints"
  value       = aws_security_group.vpc_endpoints.id
}

