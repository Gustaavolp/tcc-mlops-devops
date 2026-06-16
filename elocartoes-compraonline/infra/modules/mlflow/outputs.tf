# -----------------------------------------------------------------------------
# MLflow Tracking Server Outputs
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Tracking Server
# -----------------------------------------------------------------------------

output "tracking_server_name" {
  description = "Nome do MLflow Tracking Server"
  value       = aws_sagemaker_mlflow_tracking_server.main.tracking_server_name
}

output "tracking_server_arn" {
  description = "ARN do MLflow Tracking Server"
  value       = aws_sagemaker_mlflow_tracking_server.main.arn
}

output "tracking_server_url" {
  description = "URL do MLflow UI (browser)"
  value       = aws_sagemaker_mlflow_tracking_server.main.tracking_server_url
}

output "mlflow_tracking_uri" {
  description = "Tracking URI para clientes Python MLflow (mlflow.set_tracking_uri)"
  value       = "aws://sagemaker/${aws_sagemaker_mlflow_tracking_server.main.tracking_server_name}"
}

# -----------------------------------------------------------------------------
# IAM
# -----------------------------------------------------------------------------

output "execution_role_arn" {
  description = "ARN da IAM Execution Role (use em notebooks, SageMaker Studio, etc.)"
  value       = aws_iam_role.execution.arn
}

# -----------------------------------------------------------------------------
# S3 Artifacts
# -----------------------------------------------------------------------------

output "artifact_bucket_name" {
  description = "Nome do S3 bucket de artifacts"
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_bucket_arn" {
  description = "ARN do S3 bucket de artifacts"
  value       = aws_s3_bucket.artifacts.arn
}
