# -----------------------------------------------------------------------------
# SQS Queue Outputs
# -----------------------------------------------------------------------------

# Main Queue
output "queue_arn" {
  description = "ARN da fila SQS"
  value       = aws_sqs_queue.main.arn
}

output "queue_url" {
  description = "URL da fila SQS"
  value       = aws_sqs_queue.main.url
}

output "queue_name" {
  description = "Nome da fila SQS"
  value       = aws_sqs_queue.main.name
}

# DLQ
output "dlq_arn" {
  description = "ARN da DLQ"
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_url" {
  description = "URL da DLQ"
  value       = aws_sqs_queue.dlq.url
}
