# =============================================================================
# TERRAFORM VARIABLES - PLATFORM STAGING (sa-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "staging"
aws_region     = "sa-east-1"
aws_account_id = "888577064416"

# EKS Configuration
cluster_version     = "1.32"
node_instance_types = ["t3.xlarge"] # 4 vCPU, 16GB RAM - otimizado para testes de latencia
node_min_size       = 2             # 2 nodes base para 6 inference pods (idle)
node_max_size       = 4             # Autoscaler adiciona nodes quando HPA escala pods
node_desired_size   = 2             # 2 nodes: 6 pods × 1000m = 6000m (cabe em 2 t3.xlarge)

# EKS Access Entries - Controle de acesso ao cluster via EKS Access API
eks_access_entries = {
  sso-admin = {
    principal_arn = "arn:aws:iam::888577064416:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_SSO-MVP_AF_COMPRA_ONLINE_8e043dceed4ac97d"
    policy_associations = {
      cluster-admin = {
        policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
        access_scope = {
          type = "cluster"
        }
      }
    }
  }
}

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "staging"
  ManagedBy   = "Terraform"
  Stack       = "Platform"
  Region      = "sa-east-1"
}

# -----------------------------------------------------------------------------
# API Gateway Configuration
# -----------------------------------------------------------------------------
api_keys = {
  "elo-backend" = {
    enabled     = true
    description = "API Key para backend Elo - STAGING"
  }
  "testing" = {
    enabled     = true
    description = "API Key para testes automatizados - STAGING"
  }
}

# -----------------------------------------------------------------------------
# SQS Configuration
# -----------------------------------------------------------------------------
sqs_fifo_queue                    = true    # Garante ordenacao de mensagens
sqs_content_based_deduplication   = true    # Garante idempotencia
sqs_visibility_timeout_seconds    = 300     # 5 minutos para processar
sqs_message_retention_seconds     = 1209600 # 14 dias
sqs_receive_wait_time_seconds     = 20      # Long polling
sqs_max_receive_count             = 3       # 3 tentativas antes de ir para DLQ
sqs_delay_seconds                 = 0       # Sem delay antes da mensagem ficar disponivel
sqs_max_message_size              = 262144  # 256KB - tamanho maximo da mensagem
sqs_dlq_message_retention_seconds = 1209600 # 14 dias de retencao na DLQ

# -----------------------------------------------------------------------------
# NLB Configuration
# -----------------------------------------------------------------------------
nlb_listener_port         = 80 # Porta que o VPC Link acessa
nlb_health_check_interval = 30 # Segundos entre health checks
nlb_health_check_timeout  = 10 # Segundos de timeout
nlb_healthy_threshold     = 3  # Checks para considerar saudavel
nlb_unhealthy_threshold   = 3  # Checks para considerar nao saudavel

# -----------------------------------------------------------------------------
# Firehose Configuration
# -----------------------------------------------------------------------------
firehose_buffer_size_mb          = 1  # MB (minimo suportado) - entrega rapida para staging
firehose_buffer_interval_seconds = 60 # Segundos (minimo suportado)

# -----------------------------------------------------------------------------
# API Gateway Extended Configuration
# -----------------------------------------------------------------------------
api_gateway_log_retention_days              = 30     # 30 dias de retencao para analise
api_gateway_usage_plan_quota_limit          = 100000 # 100K requests/mes (staging)
api_gateway_usage_plan_throttle_burst_limit = 1000   # Burst por API Key
api_gateway_usage_plan_throttle_rate_limit  = 500    # Rate por API Key

# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------
inference_service_port = 8000 # Porta do servico inference (NLB -> EKS pods)

# -----------------------------------------------------------------------------
# Athena Configuration
# -----------------------------------------------------------------------------
athena_bytes_scanned_limit             = 10737418240      # 10 GB limite por query
athena_force_destroy                   = true             # Permitir deletar bucket em staging
athena_inference_logs_table_name       = "inference_logs" # Nome da tabela Glue
athena_partition_projection_year_range = "2024,2030"      # Range de anos para partition projection

# -----------------------------------------------------------------------------
# SQS Alarm Configuration
# -----------------------------------------------------------------------------
sqs_alarm_queue_depth_threshold  = 1000 # Mensagens na fila para alarme
sqs_alarm_age_threshold_seconds  = 600  # 10 minutos - idade maxima da mensagem
sqs_dlq_alarm_threshold          = 0    # Qualquer mensagem na DLQ dispara alarme
sqs_alarm_evaluation_periods     = 2    # Periodos para avaliar alarmes de fila
sqs_alarm_period_seconds         = 300  # 5 minutos - intervalo de coleta de metricas
sqs_dlq_alarm_evaluation_periods = 1    # Periodos para avaliar alarme da DLQ
sqs_dlq_alarm_period_seconds     = 60   # 1 minuto - intervalo de coleta da DLQ

# -----------------------------------------------------------------------------
# API Gateway Stage Configuration
# -----------------------------------------------------------------------------
api_gateway_stage_name                 = "v1"  # Stage do API Gateway para metricas
api_gateway_stage_throttle_burst_limit = 5000  # Burst limit do stage (requests simultaneas)
api_gateway_stage_throttle_rate_limit  = 10000 # Rate limit do stage (requests/segundo)

# Integration Timeouts - Fail fast para deteccao de pods travados
# SLA p95 < 500ms | p99 ~400ms | p99.9 ~637ms | 3s = margem segura para retries boto3
api_gateway_integration_timeout_ms  = 3000 # 3s - authorize-purchase (fail fast)
api_gateway_health_check_timeout_ms = 5000 # 5s - health check (mais permissivo)

# -----------------------------------------------------------------------------
# Glue ETL Configuration
# -----------------------------------------------------------------------------
glue_version           = "5.0"  # Versao do AWS Glue
glue_worker_type       = "G.1X" # Tipo de worker (G.1X = 4 vCPU, 16GB)
glue_number_of_workers = 10     # Workers para processamento paralelo
glue_job_timeout       = 480    # Timeout em minutos (8 horas)
glue_max_retries       = 0      # Sem retries automaticos (jobs idempoentes)

# Glue Job Names e Schedule
glue_training_job_name = "job_training_test_1" # Job: merge inference_logs -> transformed_zone
glue_training_schedule = "cron(0 8 ? * SUN *)" # Domingo 08:00 UTC (05:00 BRT)

# -----------------------------------------------------------------------------
# DynamoDB Schema Configuration
# -----------------------------------------------------------------------------
dynamodb_hash_key  = "acctID"               # Partition key: Account ID
dynamodb_range_key = "threeDSServerTransID" # Sort key: 3DS Server Transaction ID

# -----------------------------------------------------------------------------
# Data Lake S3 Prefixes
# -----------------------------------------------------------------------------
s3_prefix_transformed_zone = "transformed_zone" # Dados processados (Delta Lake)
s3_prefix_inference_logs   = "inference_logs"   # Logs de inferencia
