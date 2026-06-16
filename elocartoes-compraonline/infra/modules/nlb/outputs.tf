# =============================================================================
# NLB Module - Outputs
# =============================================================================
# Outputs do Network Load Balancer para uso em outros modulos
# Principais outputs: nlb_arn (para VPC Link) e nlb_dns_name (para integracao)
# =============================================================================

# -----------------------------------------------------------------------------
# NLB Outputs
# -----------------------------------------------------------------------------

output "nlb_arn" {
  description = "ARN do Network Load Balancer (usado para criar VPC Link)"
  value       = aws_lb.this.arn
}

output "nlb_arn_suffix" {
  description = "ARN suffix do NLB (para metricas CloudWatch)"
  value       = aws_lb.this.arn_suffix
}

output "nlb_dns_name" {
  description = "DNS name do NLB (usado na integracao do API Gateway)"
  value       = aws_lb.this.dns_name
}

output "nlb_zone_id" {
  description = "Zone ID do NLB (para Route53 se necessario)"
  value       = aws_lb.this.zone_id
}

# -----------------------------------------------------------------------------
# Target Group Outputs
# -----------------------------------------------------------------------------

output "target_group_arn" {
  description = "ARN do Target Group"
  value       = aws_lb_target_group.this.arn
}

output "target_group_arn_suffix" {
  description = "ARN suffix do Target Group (para metricas CloudWatch)"
  value       = aws_lb_target_group.this.arn_suffix
}
