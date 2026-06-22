# -----------------------------------------------------------------------------
# Streaming Configuration - Kinesis Firehose
# -----------------------------------------------------------------------------
# Delivery Stream para envio em batch de inference logs para S3.
#
# Fluxo:
#   Inference -> SQS -> Process Worker -> Firehose -> S3 (inference_logs/)
#
# Destino: s3://bucket/inference_logs/year=YYYY/month=MM/day=DD/hour=HH/
#
# Formato: Hive-style partitioning (padrao industria: Hadoop, Spark, Presto)
#
# Beneficios:
#   - Reducao de ~99% nas chamadas S3 PUT
#   - Particionamento Hive-style (year=, month=, day=, hour=)
#   - Compativel com MSCK REPAIR TABLE e AWS Glue Crawler
#   - Logging de erros no CloudWatch
#   - Tabela inference_logs no Athena usa Partition Projection
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Firehose - Inference Logs
# -----------------------------------------------------------------------------
# Recebe logs de inferencia do Process Worker e entrega em batch para S3.

module "firehose_inference" {
  source = "../../../modules/firehose"

  environment = var.environment

  # Nome do stream (explícito)
  stream_name         = "${var.project_name}-inference-firehose-${var.environment}"
  purpose_description = "Inference Logs Batch Delivery"

  # S3 Destination - MESMO bucket, prefixo diferente
  s3_bucket_arn = local.s3_processed_bucket_arn
  s3_prefix     = var.s3_prefix_inference_logs

  # Buffer Configuration (valores definidos em terraform.tfvars)
  buffer_size_mb          = var.firehose_buffer_size_mb
  buffer_interval_seconds = var.firehose_buffer_interval_seconds

  # Tags
  tags = var.common_tags
}
