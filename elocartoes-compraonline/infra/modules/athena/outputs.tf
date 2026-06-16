# -----------------------------------------------------------------------------
# Athena Module - Outputs
# -----------------------------------------------------------------------------

output "database_name" {
  description = "Nome do Glue Database"
  value       = aws_glue_catalog_database.main.name
}

output "inference_logs_table_name" {
  description = "Nome da Glue Table (inference_logs)"
  value       = aws_glue_catalog_table.inference_logs.name
}

output "workgroup_name" {
  description = "Nome do Athena Workgroup"
  value       = aws_athena_workgroup.main.name
}

output "results_bucket_name" {
  description = "Nome do bucket S3 para resultados"
  value       = aws_s3_bucket.athena_results.id
}

