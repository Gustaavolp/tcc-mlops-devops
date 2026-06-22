# -----------------------------------------------------------------------------
# Main Queue (FIFO)
# -----------------------------------------------------------------------------
# Fila FIFO para transacoes de fraude
# - Idempotencia: content_based_deduplication evita duplicatas
# - Ordenacao: FIFO garante processamento na ordem correta

resource "aws_sqs_queue" "main" {
  name                        = var.queue_name
  fifo_queue                  = var.fifo_queue
  content_based_deduplication = var.content_based_deduplication

  # Timing
  message_retention_seconds  = var.message_retention_seconds
  visibility_timeout_seconds = var.visibility_timeout_seconds
  delay_seconds              = var.delay_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  max_message_size           = var.max_message_size

  # Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(
    var.tags,
    {
      Name        = var.queue_name
      Environment = var.environment
      Purpose     = "Transaction Queue"
      Type        = "FIFO"
    }
  )
}

# -----------------------------------------------------------------------------
# Dead Letter Queue (DLQ)
# -----------------------------------------------------------------------------
# Recebe mensagens que falharam apos N tentativas

resource "aws_sqs_queue" "dlq" {
  name                        = var.dlq_name
  fifo_queue                  = var.fifo_queue
  content_based_deduplication = var.content_based_deduplication

  message_retention_seconds  = var.dlq_message_retention_seconds
  visibility_timeout_seconds = var.visibility_timeout_seconds
  delay_seconds              = 0 # DLQ nao precisa de delay
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  max_message_size           = var.max_message_size

  tags = merge(
    var.tags,
    {
      Name        = var.dlq_name
      Environment = var.environment
      Purpose     = "Dead Letter Queue"
      Type        = "FIFO-DLQ"
    }
  )
}


# -----------------------------------------------------------------------------
# CloudWatch Alarms
# -----------------------------------------------------------------------------

# Alarme 1: Queue depth (muitas mensagens acumuladas)
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "${var.queue_name}-high-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = var.alarm_period_seconds
  statistic           = "Average"
  threshold           = var.alarm_queue_depth_threshold
  alarm_description   = "Fila SQS com muitas mensagens acumuladas"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.main.name
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.queue_name}-alarm-depth"
    }
  )
}

# Alarme 2: Message age (mensagens antigas não processadas)
resource "aws_cloudwatch_metric_alarm" "message_age" {
  alarm_name          = "${var.queue_name}-old-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.alarm_evaluation_periods
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = var.alarm_period_seconds
  statistic           = "Maximum"
  threshold           = var.alarm_age_threshold_seconds
  alarm_description   = "Mensagens antigas não processadas na fila SQS"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.main.name
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.queue_name}-alarm-age"
    }
  )
}

# Alarme 3: DLQ nao vazia (mensagens falhando)
resource "aws_cloudwatch_metric_alarm" "dlq_not_empty" {
  alarm_name          = "${var.dlq_name}-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.dlq_alarm_evaluation_periods
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = var.dlq_alarm_period_seconds
  statistic           = "Average"
  threshold           = var.dlq_alarm_threshold
  alarm_description   = "DLQ recebeu mensagens falhadas - investigar"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.dlq_name}-alarm"
    }
  )
}
