# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# CloudWatch Log Group for Firehose Errors
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "firehose" {
  name              = "/aws/kinesisfirehose/${var.stream_name}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name        = "${var.stream_name}-logs"
      Environment = var.environment
      Purpose     = "Firehose Error Logs"
    }
  )
}

resource "aws_cloudwatch_log_stream" "firehose_s3" {
  name           = "S3Delivery"
  log_group_name = aws_cloudwatch_log_group.firehose.name
}

# -----------------------------------------------------------------------------
# IAM Role for Firehose
# -----------------------------------------------------------------------------

resource "aws_iam_role" "firehose" {
  name = "${var.stream_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "firehose.amazonaws.com"
      }
      Condition = {
        StringEquals = {
          "sts:ExternalId" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })

  # SCP bloqueia iam:TagRole, então ignoramos mudanças de tags em recursos existentes
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# -----------------------------------------------------------------------------
# IAM Policy Attachments (managed policies devido a SCP)
# NOTA: Nomes mantidos para evitar detach/attach (SCP bloqueia DetachRolePolicy)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "firehose_s3_full_access" {
  role       = aws_iam_role.firehose.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "firehose_cloudwatch_logs" {
  role       = aws_iam_role.firehose.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# -----------------------------------------------------------------------------
# Kinesis Firehose Delivery Stream
# -----------------------------------------------------------------------------
# Recebe records e entrega em batch para S3

resource "aws_kinesis_firehose_delivery_stream" "main" {
  name        = var.stream_name
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = var.s3_bucket_arn

    # Prefix com particionamento Hive-style (year=YYYY/month=MM/day=DD/hour=HH)
    # Formato padrão da indústria (Hadoop, Spark, Hive, Presto, AWS Glue)
    # Isso cria estrutura: landing_zone/year=2026/month=01/day=07/hour=19/
    prefix              = "${var.s3_prefix}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "${var.s3_prefix}/errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"

    buffering_size     = var.buffer_size_mb
    buffering_interval = var.buffer_interval_seconds
    compression_format = var.compression_format
    s3_backup_mode     = var.s3_backup_mode

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose.name
      log_stream_name = aws_cloudwatch_log_stream.firehose_s3.name
    }
  }

  tags = merge(
    var.tags,
    {
      Name        = var.stream_name
      Environment = var.environment
      Purpose     = var.purpose_description
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.firehose_s3_full_access,
    aws_iam_role_policy_attachment.firehose_cloudwatch_logs
  ]
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# Alarme: Falha na entrega para S3
# Configuracoes definidas via variaveis para flexibilidade por ambiente
resource "aws_cloudwatch_metric_alarm" "delivery_to_s3" {
  alarm_name          = "${var.stream_name}-delivery-failed"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "DeliveryToS3.Success"
  namespace           = "AWS/Firehose"
  period              = var.alarm_period_seconds
  statistic           = "Average"
  threshold           = var.alarm_delivery_success_threshold
  alarm_description   = "Firehose falhou ao entregar records para S3"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DeliveryStreamName = aws_kinesis_firehose_delivery_stream.main.name
  }
}
