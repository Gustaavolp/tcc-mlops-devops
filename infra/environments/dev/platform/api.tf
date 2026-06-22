# -----------------------------------------------------------------------------
# API Gateway Configuration
# -----------------------------------------------------------------------------
# Este arquivo contém módulo de API Gateway
#
# Arquitetura (trafego interno via VPC Link):
#   API Gateway -> VPC Link -> NLB (privado) -> EKS Pods (porta 8000)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# API Gateway Module
# -----------------------------------------------------------------------------

module "api_gateway" {
  source = "../../../modules/api-gateway"

  environment = var.environment

  api_name        = "${var.project_name}-api-${var.environment}"
  api_description = "Fraud Detection API - Real-time fraud scoring for online purchases"

  # Endpoint Type
  endpoint_configuration_type = "REGIONAL"

  # ---------------------------------------------------------------------------
  # VPC Link Configuration (trafego interno)
  # ---------------------------------------------------------------------------
  # Trafego interno via VPC Link -> NLB -> EKS Pods
  nlb_arn      = local.nlb_arn
  nlb_dns_name = local.nlb_dns_name

  # Stage (valor definido em terraform.tfvars)
  stage_name = var.api_gateway_stage_name

  # Access Logs - Desabilitado (account-level CW Logs role nao configurado)
  enable_access_logs = false
  log_retention_days = var.api_gateway_log_retention_days

  # Throttling (stage level - valores definidos em terraform.tfvars)
  throttle_burst_limit = var.api_gateway_stage_throttle_burst_limit
  throttle_rate_limit  = var.api_gateway_stage_throttle_rate_limit

  # ---------------------------------------------------------------------------
  # Usage Plan (Rate Limiting por API Key)
  # ---------------------------------------------------------------------------
  # Habilita controle de acesso e rate limiting por cliente via API Keys
  # NOTA: API Keys são para identificação/throttling, NÃO para autenticação
  # Valores definidos em terraform.tfvars
  usage_plan_quota_limit          = var.api_gateway_usage_plan_quota_limit
  usage_plan_quota_period         = "MONTH"
  usage_plan_throttle_burst_limit = var.api_gateway_usage_plan_throttle_burst_limit
  usage_plan_throttle_rate_limit  = var.api_gateway_usage_plan_throttle_rate_limit

  # API Keys (definidas em terraform.tfvars)
  api_keys = var.api_keys

  # ---------------------------------------------------------------------------
  # Integration Timeouts (fail fast)
  # ---------------------------------------------------------------------------
  # 3s para authorize-purchase: 11x sobre p50, 6x sobre p95, cobre retries boto3
  # 5s para health check: margem permissiva (responde em <10ms normalmente)
  integration_timeout_ms  = var.api_gateway_integration_timeout_ms
  health_check_timeout_ms = var.api_gateway_health_check_timeout_ms

  tags = var.common_tags

  # Depende do NLB estar criado para o VPC Link
  depends_on = [module.nlb]
}
