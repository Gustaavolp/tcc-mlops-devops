# -----------------------------------------------------------------------------
# API Gateway Outputs
# -----------------------------------------------------------------------------

# REST API
output "rest_api_id" {
  description = "ID da REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "rest_api_arn" {
  description = "ARN da REST API"
  value       = aws_api_gateway_rest_api.main.arn
}

# Stage
output "stage_name" {
  description = "Nome do stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "stage_invoke_url" {
  description = "URL de invocação do stage"
  value       = aws_api_gateway_stage.main.invoke_url
}

# Endpoints
output "authorize_purchase_endpoint_url" {
  description = "URL completa do endpoint POST /authorize-purchase"
  value       = "${aws_api_gateway_stage.main.invoke_url}/authorize-purchase"
}

output "health_endpoint_url" {
  description = "URL completa do endpoint GET /health"
  value       = "${aws_api_gateway_stage.main.invoke_url}/health"
}

# API Keys
output "api_key_values" {
  description = "Mapa de API Key names para valores (use com cuidado - sensitive)"
  value       = { for k, v in aws_api_gateway_api_key.keys : k => v.value }
  sensitive   = true
}
