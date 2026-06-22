# -----------------------------------------------------------------------------
# Kinesis Firehose Module - Outputs
# -----------------------------------------------------------------------------

output "delivery_stream_name" {
  description = "Nome do Firehose Delivery Stream"
  value       = aws_kinesis_firehose_delivery_stream.main.name
}

output "delivery_stream_arn" {
  description = "ARN do Firehose Delivery Stream"
  value       = aws_kinesis_firehose_delivery_stream.main.arn
}
