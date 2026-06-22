# =============================================================================
# MLOPS OUTPUTS
# =============================================================================

# MLflow
output "mlflow_tracking_server_arn" {
  description = "ARN do MLflow Tracking Server (para Lambda MLFLOW_TRACKING_URI)"
  value       = module.mlflow.tracking_server_arn
}

output "mlflow_execution_role_arn" {
  description = "ARN da execution role do MLflow"
  value       = module.mlflow.execution_role_arn
}
