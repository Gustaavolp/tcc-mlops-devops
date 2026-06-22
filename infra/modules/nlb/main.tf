# =============================================================================
# NLB Module - Main
# =============================================================================
# Network Load Balancer interno para integracao com VPC Link do API Gateway
# Encaminha trafego diretamente para os pods de inference (target_type = ip)
#
# Arquitetura:
#   API Gateway -> VPC Link -> NLB (privado) -> EKS Pods (porta 8000)
#
# O AWS Load Balancer Controller registra os pod IPs automaticamente
# via TargetGroupBinding CRD (gerenciado na stack platform-k8s)
# =============================================================================

# -----------------------------------------------------------------------------
# Network Load Balancer (Interno)
# -----------------------------------------------------------------------------
# NLB deve ser interno para funcionar com VPC Link do API Gateway
# Subnets devem ser privadas para garantir que trafego nao saia para internet
# -----------------------------------------------------------------------------

resource "aws_lb" "this" {
  name               = var.name
  internal           = true # SEMPRE interno - VPC Link requer NLB privado
  load_balancer_type = "network"
  subnets            = var.subnet_ids

  # Cross-zone load balancing distribui trafego entre AZs
  enable_cross_zone_load_balancing = var.enable_cross_zone_load_balancing

  # Protecao contra delecao acidental
  enable_deletion_protection = var.enable_deletion_protection

  tags = merge(var.tags, {
    Name        = var.name
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Target Group
# -----------------------------------------------------------------------------
# Target Group do NLB - encaminha diretamente para pods (target_type = ip)
# AWS Load Balancer Controller registra pod IPs via TargetGroupBinding CRD
# Health check HTTP verifica saude dos pods via endpoint /health
# -----------------------------------------------------------------------------

resource "aws_lb_target_group" "this" {
  name        = var.target_group_name
  port        = var.target_port
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  # Deregistration delay para drenar conexoes antes de remover targets
  deregistration_delay = var.deregistration_delay

  # Health check HTTP nos targets
  health_check {
    enabled             = true
    protocol            = "HTTP"
    path                = var.health_check_path
    port                = "traffic-port"
    healthy_threshold   = var.healthy_threshold
    unhealthy_threshold = var.unhealthy_threshold
    interval            = var.health_check_interval
    timeout             = var.health_check_timeout
  }

  tags = merge(var.tags, {
    Name        = var.target_group_name
    Environment = var.environment
  })

  lifecycle {
    create_before_destroy = true
  }
}

# -----------------------------------------------------------------------------
# Listener TCP
# -----------------------------------------------------------------------------
# NLB usa protocolo TCP (Layer 4) para encaminhar trafego
# Porta padrao 80 para HTTP
# -----------------------------------------------------------------------------

resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = var.listener_port
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-listener-${var.listener_port}"
    Environment = var.environment
  })
}
