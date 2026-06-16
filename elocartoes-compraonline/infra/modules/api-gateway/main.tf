# -----------------------------------------------------------------------------
# API Gateway REST API Module
# -----------------------------------------------------------------------------
# Este modulo cria uma API Gateway REST API com integracao privada via VPC Link:
# - HTTP Proxy para backend via VPC Link (trafego interno)
# - Rate limiting e throttling (stage-level e per-API Key via Usage Plan)
# - CloudWatch logging
# - API Keys para identificacao de clientes (opcional)
#
# Arquitetura (trafego interno):
#   Cliente -> API Gateway -> VPC Link -> NLB (privado) -> EKS Pods (porta 8000)
#
# NOTA: Este modulo usa APENAS trafego interno via VPC Link.
# O trafego entre API Gateway e o backend nao passa pela internet publica.
# NOTA: CORS nao e necessario pois a integracao e server-to-server (backend Elo).
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CloudWatch Log Group para API Gateway
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_access_logs ? 1 : 0

  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "/aws/apigateway/${var.api_name}"
    Environment = var.environment
    Service     = "API Gateway"
  })
}

# -----------------------------------------------------------------------------
# VPC Link (integracao privada com NLB)
# -----------------------------------------------------------------------------
# VPC Link permite que o API Gateway acesse recursos em VPC privada
# Requer NLB (Network Load Balancer) como target
#
# NOTA: VPC Link pode levar 2-5 minutos para ficar disponivel (status AVAILABLE)
# -----------------------------------------------------------------------------

resource "aws_api_gateway_vpc_link" "main" {
  name        = "${var.api_name}-vpc-link"
  description = "VPC Link para integracao privada com NLB - ${var.environment}"
  target_arns = [var.nlb_arn]

  tags = merge(var.tags, {
    Name        = "${var.api_name}-vpc-link"
    Environment = var.environment
    Service     = "API Gateway"
    Component   = "VPC Link"
  })
}

# -----------------------------------------------------------------------------
# REST API
# -----------------------------------------------------------------------------

resource "aws_api_gateway_rest_api" "main" {
  name        = var.api_name
  description = var.api_description

  endpoint_configuration {
    types = [var.endpoint_configuration_type]
  }

  # Configuração de API policy (opcional)
  # policy = jsonencode({})

  tags = merge(var.tags, {
    Name        = var.api_name
    Environment = var.environment
    Service     = "API Gateway"
  })
}


# -----------------------------------------------------------------------------
# Resources (/authorize-purchase, /health)
# -----------------------------------------------------------------------------
# NOTA: Recursos na raiz (sem /v1) pois o stage já é "v1"
# URLs finais: /v1/authorize-purchase, /v1/health

# Resource: /authorize-purchase (stage v1 → /v1/authorize-purchase)
resource "aws_api_gateway_resource" "authorize_purchase" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "authorize-purchase"
}

# Resource: /health (stage v1 → /v1/health)
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "health"
}

# -----------------------------------------------------------------------------
# Method: POST /v1/authorize-purchase
# -----------------------------------------------------------------------------

resource "aws_api_gateway_method" "post_authorize_purchase" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.authorize_purchase.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

# Integration: POST /v1/authorize-purchase -> Backend via VPC Link
resource "aws_api_gateway_integration" "post_authorize_purchase" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.authorize_purchase.id
  http_method = aws_api_gateway_method.post_authorize_purchase.http_method

  # HTTP Proxy via VPC Link (trafego interno)
  type                    = "HTTP_PROXY"
  integration_http_method = "POST"
  uri                     = "http://${var.nlb_dns_name}/v1/authorize-purchase"

  # VPC Link para trafego interno
  connection_type = "VPC_LINK"
  connection_id   = aws_api_gateway_vpc_link.main.id

  timeout_milliseconds = var.integration_timeout_ms

  request_parameters = {
    "integration.request.header.X-Forwarded-For" = "context.identity.sourceIp"
    "integration.request.header.X-Trace-Id"      = "context.requestId"
  }
}

# Method Response: POST /v1/authorize-purchase
resource "aws_api_gateway_method_response" "post_authorize_purchase_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.authorize_purchase.id
  http_method = aws_api_gateway_method.post_authorize_purchase.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "post_authorize_purchase_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.authorize_purchase.id
  http_method = aws_api_gateway_method.post_authorize_purchase.http_method
  status_code = aws_api_gateway_method_response.post_authorize_purchase_200.status_code

  depends_on = [aws_api_gateway_integration.post_authorize_purchase]
}

# -----------------------------------------------------------------------------
# Method: GET /health
# -----------------------------------------------------------------------------

resource "aws_api_gateway_method" "get_health" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.health.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "get_health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.get_health.http_method

  # HTTP Proxy via VPC Link (trafego interno)
  type                    = "HTTP_PROXY"
  integration_http_method = "GET"
  uri                     = "http://${var.nlb_dns_name}/health"

  # VPC Link para trafego interno
  connection_type = "VPC_LINK"
  connection_id   = aws_api_gateway_vpc_link.main.id

  timeout_milliseconds = var.health_check_timeout_ms
}

resource "aws_api_gateway_method_response" "get_health_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.get_health.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration_response" "get_health_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.get_health.http_method
  status_code = aws_api_gateway_method_response.get_health_200.status_code

  depends_on = [aws_api_gateway_integration.get_health]
}

# -----------------------------------------------------------------------------
# Deployment
# -----------------------------------------------------------------------------

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  # Forca recriacao do deployment quando resources/methods ou backend mudarem
  # NOTA: Incluido nlb_dns_name para garantir redeploy quando o backend mudar
  # Sem isso, a integration e atualizada mas o deployment nao, causando 500 Internal Server Error
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.authorize_purchase.id,
      aws_api_gateway_resource.health.id,
      aws_api_gateway_method.post_authorize_purchase.id,
      aws_api_gateway_method.get_health.id,
      aws_api_gateway_integration.post_authorize_purchase.id,
      aws_api_gateway_integration.get_health.id,
      var.nlb_dns_name,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.post_authorize_purchase,
    aws_api_gateway_method.get_health,
    aws_api_gateway_integration.post_authorize_purchase,
    aws_api_gateway_integration.get_health,
    aws_api_gateway_integration_response.post_authorize_purchase_200,
    aws_api_gateway_integration_response.get_health_200,
  ]
}

# -----------------------------------------------------------------------------
# Stage
# -----------------------------------------------------------------------------

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name


  # Access logs
  dynamic "access_log_settings" {
    for_each = var.enable_access_logs ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
      format = jsonencode({
        requestId      = "$context.requestId"
        ip             = "$context.identity.sourceIp"
        caller         = "$context.identity.caller"
        user           = "$context.identity.user"
        requestTime    = "$context.requestTime"
        httpMethod     = "$context.httpMethod"
        resourcePath   = "$context.resourcePath"
        status         = "$context.status"
        protocol       = "$context.protocol"
        responseLength = "$context.responseLength"
        latency        = "$context.integration.latency"
      })
    }
  }

  tags = merge(var.tags, {
    Name        = "${var.api_name}-${var.stage_name}"
    Environment = var.environment
    Service     = "API Gateway"
  })
}

# Method settings (para configurar throttling por method, logs, etc)
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = var.enable_access_logs ? "INFO" : "OFF"
    data_trace_enabled = var.enable_access_logs


    # Throttling settings (pode ser sobrescrito por method)
    throttling_burst_limit = var.throttle_burst_limit
    throttling_rate_limit  = var.throttle_rate_limit
  }
}

# -----------------------------------------------------------------------------
# Usage Plan (Rate Limiting por API Key)
# -----------------------------------------------------------------------------
# Usage Plan permite:
# - Definir quotas (limite de requests por período)
# - Definir throttling específico por API Key
# - Rastrear uso por cliente
#
# NOTA: API Keys NÃO devem ser usadas para autenticação/autorização
# Use apenas para identificação de clientes e rate limiting
# Para autenticação, use IAM, Cognito ou Lambda Authorizer
# -----------------------------------------------------------------------------

resource "aws_api_gateway_usage_plan" "main" {
  name        = "${var.api_name}-usage-plan"
  description = "Usage Plan para ${var.api_name} - Rate limiting por API Key"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = var.usage_plan_quota_limit
    period = var.usage_plan_quota_period
  }

  throttle_settings {
    burst_limit = var.usage_plan_throttle_burst_limit
    rate_limit  = var.usage_plan_throttle_rate_limit
  }

  tags = merge(var.tags, {
    Name        = "${var.api_name}-usage-plan"
    Environment = var.environment
    Service     = "API Gateway"
  })

  depends_on = [aws_api_gateway_stage.main]
}

# -----------------------------------------------------------------------------
# API Keys
# -----------------------------------------------------------------------------
# API Keys são criadas e associadas ao Usage Plan
# Cada key herda os limites do Usage Plan
# -----------------------------------------------------------------------------

resource "aws_api_gateway_api_key" "keys" {
  for_each = var.api_keys

  name        = "${var.api_name}-${each.key}"
  description = each.value.description
  enabled     = each.value.enabled

  tags = merge(var.tags, {
    Name        = "${var.api_name}-${each.key}"
    Environment = var.environment
    Service     = "API Gateway"
    KeyName     = each.key
  })
}

# -----------------------------------------------------------------------------
# Usage Plan Key Association
# -----------------------------------------------------------------------------
# Associa cada API Key ao Usage Plan
# -----------------------------------------------------------------------------

resource "aws_api_gateway_usage_plan_key" "keys" {
  for_each = var.api_keys

  key_id        = aws_api_gateway_api_key.keys[each.key].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}

