# -----------------------------------------------------------------------------
# Analytics Configuration - Athena
# -----------------------------------------------------------------------------
# Configura Athena para consultas SQL sobre dados do Process Service no S3
#
# TABELA:
#   - inference_logs: Logs de inferencia (inference_logs/)
#     * Formato: JSON
#     * Partition Projection habilitado (year/month/day/hour)
#     * Dados do Firehose via Process Worker
# -----------------------------------------------------------------------------

module "athena" {
  source = "../../../modules/athena"

  environment         = var.environment
  database_name       = replace("${var.project_name}_${var.environment}_db", "-", "_")
  workgroup_name      = "${var.project_name}-athena-workgroup-${var.environment}"
  results_bucket_name = "${var.project_name}-athena-results-${var.environment}-${var.aws_account_id}"

  # Bucket S3 onde os dados estao armazenados
  source_bucket_name = local.s3_processed_bucket_id

  # Configuracoes (valores definidos em terraform.tfvars)
  inference_logs_prefix           = var.s3_prefix_inference_logs
  inference_logs_table_name       = var.athena_inference_logs_table_name
  partition_projection_year_range = var.athena_partition_projection_year_range
  bytes_scanned_limit             = var.athena_bytes_scanned_limit
  force_destroy                   = var.athena_force_destroy

  tags = var.common_tags
}
