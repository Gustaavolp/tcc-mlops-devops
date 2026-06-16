# =============================================================================
# NLB Configuration - Staging (sa-east-1)
# =============================================================================
# Network Load Balancer para integracao com VPC Link do API Gateway
# Encaminha trafego diretamente para os pods de inference (target_type = ip)
#
# Arquitetura:
#   API Gateway -> VPC Link -> NLB (privado) -> EKS Pods (porta 8000)
#
# O AWS Load Balancer Controller registra os pod IPs automaticamente
# via TargetGroupBinding CRD (gerenciado na stack platform-k8s)
# =============================================================================

module "nlb" {
  source = "../../../modules/nlb"

  # Identificacao
  environment = var.environment
  name        = "${var.project_name}-nlb-${var.environment}"

  # Rede - NLB em subnets privadas para integracao com VPC Link
  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnet_ids

  # Target - Direto para pods via TargetGroupBinding (target_type = ip)
  target_group_name = "inference-nlb-tg-${var.environment}"
  target_port       = 8000 # Porta do servico inference (FastAPI)

  # Listener - Porta que o VPC Link acessa
  listener_port = var.nlb_listener_port

  # Health Check - Verifica saude dos pods via endpoint HTTP
  health_check_path     = "/health"
  health_check_interval = var.nlb_health_check_interval
  health_check_timeout  = var.nlb_health_check_timeout
  healthy_threshold     = var.nlb_healthy_threshold
  unhealthy_threshold   = var.nlb_unhealthy_threshold

  # NLB Attributes
  enable_cross_zone_load_balancing = true
  enable_deletion_protection       = false # STAGING - sem protecao

  tags = var.common_tags
}
