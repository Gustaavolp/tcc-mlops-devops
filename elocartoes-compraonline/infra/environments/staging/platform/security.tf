# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------
# Este arquivo contém módulos de segurança: IAM
# S3 buckets vêm da stack Foundation via remote_state.

# -----------------------------------------------------------------------------
# Bedrock Agent Module
# -----------------------------------------------------------------------------
# Role para Bedrock Agents com acesso ao Athena para consultas SQL.
# Usado pelo agent-consult-athena para consultar dados no Data Lake.

module "bedrock_agent" {
  source = "../../../modules/bedrock-agent"

  project_name = var.project_name
  environment  = var.environment
  tags         = var.common_tags
}

# -----------------------------------------------------------------------------
# Security Group Rule: NLB/VPC -> EKS Nodes (porta 8000)
# -----------------------------------------------------------------------------
# Permite que o NLB (via VPC Link) acesse os pods de inference na porta 8000.
# Necessario para health checks e roteamento de trafego do API Gateway.
#
# NLB nao possui Security Group proprio - o trafego chega com IP de origem
# da subnet do NLB, por isso usamos cidr_blocks com o CIDR da VPC.
# -----------------------------------------------------------------------------

resource "aws_security_group_rule" "nlb_to_nodes_inference" {
  type              = "ingress"
  from_port         = var.inference_service_port
  to_port           = var.inference_service_port
  protocol          = "tcp"
  security_group_id = module.eks.node_security_group_id
  cidr_blocks       = [data.terraform_remote_state.foundation.outputs.vpc_cidr]
  description       = "Allow NLB/VPC to access inference pods on port ${var.inference_service_port}"
}
