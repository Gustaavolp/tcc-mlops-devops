# =============================================================================
# CLOUDWATCH MONITORING - DASHBOARDS
# =============================================================================
# Este arquivo contém recursos de observabilidade para a stack Platform:
#   - CloudWatch Dashboard Infrastructure: SQS, DynamoDB, Firehose
#   - CloudWatch Dashboard API Performance: API Gateway, NLB
#
# Métricas monitoradas:
#   - SQS: Queue depth, message age, DLQ
#   - DynamoDB: Read/Write operations, throttling
#   - Firehose: Delivery success, incoming records
#   - API Gateway: Count, Latency (p50/p95/p99), 4XX/5XX errors
#   - NLB: HealthyHostCount, ProcessedBytes, TCP Resets, Active Connections
#
# NOTA: Criado em 2026-01-22 conforme requisito de observabilidade do escopo.
# Referência: ESCOPO_FASE2_COMPRA_ONLINE.md linhas 37-39
# =============================================================================

# =============================================================================
# LOCALS - Nomes dos recursos para métricas
# =============================================================================

locals {
  # Nomes dos recursos (derivados dos módulos)
  sqs_queue_name          = module.sqs.queue_name
  sqs_dlq_name            = "${var.project_name}-resultset-${var.environment}-dlq.fifo"
  dynamodb_table_name     = module.dynamodb.table_name
  firehose_inference_name = module.firehose_inference.delivery_stream_name

  # API Gateway (para métricas AWS/ApiGateway)
  api_gateway_name  = "${var.project_name}-api-${var.environment}"
  api_gateway_stage = var.api_gateway_stage_name

  # NLB (para metricas AWS/NetworkELB)
  nlb_arn_suffix          = module.nlb.nlb_arn_suffix
  nlb_target_group_suffix = module.nlb.target_group_arn_suffix

  # Dashboard configuration
  dashboard_name          = "${var.project_name}-infrastructure-${var.environment}"
  dashboard_api_perf_name = "${var.project_name}-api-performance-${var.environment}"
}

# =============================================================================
# CLOUDWATCH DASHBOARD - INFRASTRUCTURE
# =============================================================================
# Dashboard para monitoramento da infraestrutura base:
#   - SQS: Fila de processamento e DLQ
#   - DynamoDB: Feature store
#   - Firehose: Streaming de dados
#
# Layout: 4 colunas x N linhas (cada widget ocupa width=6 de 24 total)
# =============================================================================

resource "aws_cloudwatch_dashboard" "infrastructure" {
  dashboard_name = local.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      # =========================================================================
      # ROW 1: Título e Resumo
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# Infrastructure Dashboard - ${var.project_name} (${var.environment})\nMonitoramento de SQS, DynamoDB e Firehose | Atualizado automaticamente"
        }
      },

      # =========================================================================
      # ROW 2: SQS Metrics
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 1
        width  = 24
        height = 1
        properties = {
          markdown = "## SQS - Fila de Processamento"
        }
      },
      # SQS: Queue Depth (mensagens visíveis)
      {
        type   = "metric"
        x      = 0
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Queue Depth (Messages Visible)"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", local.sqs_queue_name, {
              stat   = "Average"
              period = 60
              color  = "#2ca02c"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Warning (1000)"
                value = 1000
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      # SQS: Message Age (idade da mensagem mais antiga)
      {
        type   = "metric"
        x      = 6
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Oldest Message Age (seconds)"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", local.sqs_queue_name, {
              stat   = "Maximum"
              period = 60
              color  = "#1f77b4"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Warning (600s)"
                value = 600
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      # SQS: Messages Sent/Received
      {
        type   = "metric"
        x      = 12
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Messages Sent vs Received"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", local.sqs_queue_name, {
              stat   = "Sum"
              period = 300
              color  = "#2ca02c"
              label  = "Sent"
            }],
            ["AWS/SQS", "NumberOfMessagesReceived", "QueueName", local.sqs_queue_name, {
              stat   = "Sum"
              period = 300
              color  = "#1f77b4"
              label  = "Received"
            }]
          ]
          view = "timeSeries"
        }
      },
      # SQS: DLQ Depth
      {
        type   = "metric"
        x      = 18
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "DLQ Depth (Failed Messages)"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", local.sqs_dlq_name, {
              stat   = "Average"
              period = 60
              color  = "#d62728"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Critical (> 0)"
                value = 1
                color = "#d62728"
              }
            ]
          }
        }
      },

      # =========================================================================
      # ROW 3: DynamoDB Metrics
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 8
        width  = 24
        height = 1
        properties = {
          markdown = "## DynamoDB - Feature Store"
        }
      },
      # DynamoDB: Read/Write Operations
      {
        type   = "metric"
        x      = 0
        y      = 9
        width  = 8
        height = 6
        properties = {
          title  = "Read vs Write Operations"
          region = var.aws_region
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", local.dynamodb_table_name, {
              stat   = "Sum"
              period = 60
              color  = "#1f77b4"
              label  = "Reads"
            }],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", local.dynamodb_table_name, {
              stat   = "Sum"
              period = 60
              color  = "#2ca02c"
              label  = "Writes"
            }]
          ]
          view = "timeSeries"
        }
      },
      # DynamoDB: Successful Requests
      {
        type   = "metric"
        x      = 8
        y      = 9
        width  = 8
        height = 6
        properties = {
          title  = "Successful Request Latency (ms)"
          region = var.aws_region
          metrics = [
            ["AWS/DynamoDB", "SuccessfulRequestLatency", "TableName", local.dynamodb_table_name, "Operation", "GetItem", {
              stat   = "Average"
              period = 60
              color  = "#1f77b4"
              label  = "GetItem"
            }],
            ["AWS/DynamoDB", "SuccessfulRequestLatency", "TableName", local.dynamodb_table_name, "Operation", "PutItem", {
              stat   = "Average"
              period = 60
              color  = "#2ca02c"
              label  = "PutItem"
            }],
            ["AWS/DynamoDB", "SuccessfulRequestLatency", "TableName", local.dynamodb_table_name, "Operation", "Query", {
              stat   = "Average"
              period = 60
              color  = "#ff7f0e"
              label  = "Query"
            }]
          ]
          view = "timeSeries"
        }
      },
      # DynamoDB: Throttled Requests
      {
        type   = "metric"
        x      = 16
        y      = 9
        width  = 8
        height = 6
        properties = {
          title  = "Throttled Requests (should be 0)"
          region = var.aws_region
          metrics = [
            ["AWS/DynamoDB", "ThrottledRequests", "TableName", local.dynamodb_table_name, {
              stat   = "Sum"
              period = 60
              color  = "#d62728"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Critical (> 0)"
                value = 1
                color = "#d62728"
              }
            ]
          }
        }
      },

      # =========================================================================
      # ROW 4: Firehose Metrics
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 15
        width  = 24
        height = 1
        properties = {
          markdown = "## Kinesis Firehose - Data Streaming"
        }
      },
      # Firehose Inference: Delivery Success
      {
        type   = "metric"
        x      = 12
        y      = 16
        width  = 6
        height = 6
        properties = {
          title  = "Inference Logs - Delivery Success"
          region = var.aws_region
          metrics = [
            ["AWS/Firehose", "DeliveryToS3.Success", "DeliveryStreamName", local.firehose_inference_name, {
              stat   = "Average"
              period = 60
              color  = "#2ca02c"
            }]
          ]
          view = "timeSeries"
          yAxis = {
            left = {
              min = 0
              max = 1
            }
          }
        }
      },
      # Firehose Inference: Incoming Records
      {
        type   = "metric"
        x      = 18
        y      = 16
        width  = 6
        height = 6
        properties = {
          title  = "Inference Logs - Incoming Records"
          region = var.aws_region
          metrics = [
            ["AWS/Firehose", "IncomingRecords", "DeliveryStreamName", local.firehose_inference_name, {
              stat   = "Sum"
              period = 60
              color  = "#1f77b4"
            }]
          ]
          view = "timeSeries"
        }
      }
    ]
  })
}

# =============================================================================
# CLOUDWATCH DASHBOARD - API PERFORMANCE
# =============================================================================
# Dashboard para monitoramento de performance da API:
#   - API Gateway: Latencia (p50/p95/p99), throughput, erros
#   - NLB: Health status, bytes processados, TCP resets, conexoes ativas
#
# Arquitetura monitorada:
#   API Gateway -> VPC Link -> NLB -> EKS Pods (direto)
#
# Layout: 4 colunas x N linhas (cada widget ocupa width=6 de 24 total)
# =============================================================================

resource "aws_cloudwatch_dashboard" "api_performance" {
  dashboard_name = local.dashboard_api_perf_name

  dashboard_body = jsonencode({
    widgets = [
      # =========================================================================
      # ROW 1: Título
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# API Performance Dashboard - ${var.project_name} (${var.environment})\nMonitoramento de API Gateway e NLB | Latencias p50/p95/p99 | Atualizado automaticamente"
        }
      },

      # =========================================================================
      # ROW 2: API Gateway - Métricas Principais
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 1
        width  = 24
        height = 1
        properties = {
          markdown = "## API Gateway - Métricas de Performance"
        }
      },
      # API Gateway: Request Count (Throughput)
      {
        type   = "metric"
        x      = 0
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Request Count (Throughput)"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "Sum"
              period = 60
              color  = "#1f77b4"
              label  = "Requests/min"
            }]
          ]
          view = "timeSeries"
        }
      },
      # API Gateway: Latency p50/p95/p99
      {
        type   = "metric"
        x      = 6
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Latency Percentiles (ms)"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p50"
              period = 60
              color  = "#2ca02c"
              label  = "p50"
            }],
            ["AWS/ApiGateway", "Latency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p95"
              period = 60
              color  = "#ff7f0e"
              label  = "p95"
            }],
            ["AWS/ApiGateway", "Latency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p99"
              period = 60
              color  = "#d62728"
              label  = "p99"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "SLO p95 (500ms)"
                value = 500
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      # API Gateway: Integration Latency (tempo no backend)
      {
        type   = "metric"
        x      = 12
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Integration Latency (Backend)"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "IntegrationLatency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p50"
              period = 60
              color  = "#2ca02c"
              label  = "p50"
            }],
            ["AWS/ApiGateway", "IntegrationLatency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p95"
              period = 60
              color  = "#ff7f0e"
              label  = "p95"
            }],
            ["AWS/ApiGateway", "IntegrationLatency", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "p99"
              period = 60
              color  = "#d62728"
              label  = "p99"
            }]
          ]
          view = "timeSeries"
        }
      },
      # API Gateway: Error Rates
      {
        type   = "metric"
        x      = 18
        y      = 2
        width  = 6
        height = 6
        properties = {
          title  = "Error Rates (4XX/5XX)"
          region = var.aws_region
          metrics = [
            ["AWS/ApiGateway", "4XXError", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "Sum"
              period = 60
              color  = "#ff7f0e"
              label  = "4XX (Client)"
            }],
            ["AWS/ApiGateway", "5XXError", "ApiName", local.api_gateway_name, "Stage", local.api_gateway_stage, {
              stat   = "Sum"
              period = 60
              color  = "#d62728"
              label  = "5XX (Server)"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Critical (5XX > 0)"
                value = 1
                color = "#d62728"
              }
            ]
          }
        }
      },

      # =========================================================================
      # ROW 3: NLB - Network Load Balancer (Direct to Pods)
      # =========================================================================
      {
        type   = "text"
        x      = 0
        y      = 8
        width  = 24
        height = 1
        properties = {
          markdown = "## NLB - Network Load Balancer (Direct to Pods)"
        }
      },
      # NLB: Target Health Status (Healthy/Unhealthy pods)
      {
        type   = "metric"
        x      = 0
        y      = 9
        width  = 6
        height = 6
        properties = {
          title  = "Target Health Status (Pods)"
          region = var.aws_region
          metrics = [
            ["AWS/NetworkELB", "HealthyHostCount", "TargetGroup", local.nlb_target_group_suffix, "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Average"
              period = 60
              color  = "#2ca02c"
              label  = "Healthy"
            }],
            ["AWS/NetworkELB", "UnHealthyHostCount", "TargetGroup", local.nlb_target_group_suffix, "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Average"
              period = 60
              color  = "#d62728"
              label  = "Unhealthy"
            }]
          ]
          view = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Min Healthy (1)"
                value = 1
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      # NLB: New Flow Count (proxy para request count)
      {
        type   = "metric"
        x      = 6
        y      = 9
        width  = 6
        height = 6
        properties = {
          title  = "New Connections (Throughput)"
          region = var.aws_region
          metrics = [
            ["AWS/NetworkELB", "NewFlowCount", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Sum"
              period = 60
              color  = "#1f77b4"
              label  = "New Flows/min"
            }]
          ]
          view = "timeSeries"
        }
      },
      # NLB: TCP Resets (indicador de problemas de conexao)
      {
        type   = "metric"
        x      = 12
        y      = 9
        width  = 6
        height = 6
        properties = {
          title  = "TCP Resets (Connection Issues)"
          region = var.aws_region
          metrics = [
            ["AWS/NetworkELB", "TCP_Client_Reset_Count", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Sum"
              period = 60
              color  = "#ff7f0e"
              label  = "Client Resets"
            }],
            ["AWS/NetworkELB", "TCP_Target_Reset_Count", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Sum"
              period = 60
              color  = "#d62728"
              label  = "Target Resets"
            }],
            ["AWS/NetworkELB", "TCP_ELB_Reset_Count", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Sum"
              period = 60
              color  = "#9467bd"
              label  = "ELB Resets"
            }]
          ]
          view = "timeSeries"
        }
      },
      # NLB: Active Connections
      {
        type   = "metric"
        x      = 18
        y      = 9
        width  = 6
        height = 6
        properties = {
          title  = "Active Connections"
          region = var.aws_region
          metrics = [
            ["AWS/NetworkELB", "ActiveFlowCount", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Average"
              period = 60
              color  = "#9467bd"
              label  = "Active Flows"
            }]
          ]
          view = "timeSeries"
        }
      },
      # NLB: Processed Bytes
      {
        type   = "metric"
        x      = 0
        y      = 15
        width  = 24
        height = 6
        properties = {
          title  = "Processed Bytes"
          region = var.aws_region
          metrics = [
            ["AWS/NetworkELB", "ProcessedBytes", "LoadBalancer", local.nlb_arn_suffix, {
              stat   = "Sum"
              period = 60
              color  = "#1f77b4"
              label  = "Bytes/min"
            }]
          ]
          view = "timeSeries"
        }
      }
    ]
  })
}

