# =============================================================================
# VARIABLES - PLATFORM STACK
# =============================================================================
# Este arquivo declara as variáveis da stack.
# Os valores são definidos em terraform.tfvars
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente"
  type        = string
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------

variable "common_tags" {
  description = "Tags comuns aplicadas a todos os recursos"
  type        = map(string)
}

# -----------------------------------------------------------------------------
# EKS Configuration
# -----------------------------------------------------------------------------

variable "cluster_version" {
  description = "Versão do Kubernetes EKS"
  type        = string
}

variable "node_instance_types" {
  description = "Tipos de instância para nodes EKS"
  type        = list(string)
}

variable "node_min_size" {
  description = "Número mínimo de nodes"
  type        = number
}

variable "node_max_size" {
  description = "Número máximo de nodes"
  type        = number
}

variable "node_desired_size" {
  description = "Número desejado de nodes"
  type        = number
}

variable "eks_access_entries" {
  description = "Map de access entries para controle de acesso ao cluster EKS (SSO roles, CI/CD roles, etc.)"
  type = map(object({
    principal_arn     = string
    kubernetes_groups = optional(list(string), [])
    policy_associations = optional(map(object({
      policy_arn = string
      access_scope = object({
        type       = string
        namespaces = optional(list(string), [])
      })
    })), {})
  }))
  default = {}
}

# -----------------------------------------------------------------------------
# API Gateway Configuration
# -----------------------------------------------------------------------------

variable "api_keys" {
  description = "Mapa de API Keys para o API Gateway"
  type = map(object({
    enabled     = bool
    description = string
  }))
}

# -----------------------------------------------------------------------------
# SQS Configuration
# -----------------------------------------------------------------------------

variable "sqs_visibility_timeout_seconds" {
  description = "Tempo em segundos que uma mensagem fica invisivel apos ser lida"
  type        = number
}

variable "sqs_message_retention_seconds" {
  description = "Tempo em segundos que uma mensagem fica retida na fila"
  type        = number
}

variable "sqs_receive_wait_time_seconds" {
  description = "Tempo em segundos para long polling"
  type        = number
}

variable "sqs_max_receive_count" {
  description = "Numero maximo de tentativas antes de enviar para DLQ"
  type        = number
}

variable "sqs_fifo_queue" {
  description = "Fila FIFO - garante ordenacao e exatamente uma entrega"
  type        = bool
}

variable "sqs_content_based_deduplication" {
  description = "Deduplicacao baseada no conteudo da mensagem - garante idempotencia"
  type        = bool
}

variable "sqs_delay_seconds" {
  description = "Tempo de delay em segundos antes da mensagem ficar disponivel"
  type        = number
}

variable "sqs_max_message_size" {
  description = "Tamanho maximo da mensagem em bytes"
  type        = number
}

variable "sqs_dlq_message_retention_seconds" {
  description = "Tempo em segundos que uma mensagem fica retida na DLQ"
  type        = number
}

# -----------------------------------------------------------------------------
# NLB Configuration
# -----------------------------------------------------------------------------

variable "nlb_listener_port" {
  description = "Porta do listener do NLB (VPC Link)"
  type        = number
}

variable "nlb_health_check_interval" {
  description = "Intervalo em segundos entre health checks do NLB"
  type        = number
}

variable "nlb_health_check_timeout" {
  description = "Timeout em segundos para health check do NLB"
  type        = number
}

variable "nlb_healthy_threshold" {
  description = "Numero de health checks consecutivos para considerar target saudavel"
  type        = number
}

variable "nlb_unhealthy_threshold" {
  description = "Numero de health checks consecutivos para considerar target nao saudavel"
  type        = number
}

# -----------------------------------------------------------------------------
# Firehose Configuration
# -----------------------------------------------------------------------------

variable "firehose_buffer_size_mb" {
  description = "Tamanho do buffer em MB para Firehose"
  type        = number
}

variable "firehose_buffer_interval_seconds" {
  description = "Intervalo do buffer em segundos para Firehose"
  type        = number
}

# -----------------------------------------------------------------------------
# API Gateway Extended Configuration
# -----------------------------------------------------------------------------

variable "api_gateway_log_retention_days" {
  description = "Dias de retencao dos logs do API Gateway no CloudWatch"
  type        = number
}

variable "api_gateway_usage_plan_quota_limit" {
  description = "Limite de quota do usage plan (requests por periodo)"
  type        = number
}

variable "api_gateway_usage_plan_throttle_burst_limit" {
  description = "Limite de burst do usage plan por API Key"
  type        = number
}

variable "api_gateway_usage_plan_throttle_rate_limit" {
  description = "Limite de rate do usage plan por API Key"
  type        = number
}

# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------

variable "inference_service_port" {
  description = "Porta do servico de inference (usada no NLB e Security Group)"
  type        = number
}

# -----------------------------------------------------------------------------
# Athena Configuration
# -----------------------------------------------------------------------------

variable "athena_bytes_scanned_limit" {
  description = "Limite em bytes de dados escaneados por query no Athena"
  type        = number
}

variable "athena_force_destroy" {
  description = "Permitir destruicao do bucket Athena mesmo com objetos"
  type        = bool
}

variable "athena_inference_logs_table_name" {
  description = "Nome da tabela Glue para inference logs"
  type        = string
}

variable "athena_partition_projection_year_range" {
  description = "Range de anos para partition projection (formato: 'YYYY,YYYY')"
  type        = string
}

# -----------------------------------------------------------------------------
# SQS Alarm Configuration
# -----------------------------------------------------------------------------

variable "sqs_alarm_queue_depth_threshold" {
  description = "Threshold de profundidade da fila para alarme CloudWatch"
  type        = number
}

variable "sqs_alarm_age_threshold_seconds" {
  description = "Threshold em segundos da idade da mensagem mais antiga para alarme"
  type        = number
}

variable "sqs_dlq_alarm_threshold" {
  description = "Threshold de mensagens na DLQ para alarme (0 = qualquer mensagem)"
  type        = number
}

variable "sqs_alarm_evaluation_periods" {
  description = "Numero de periodos para avaliar os alarmes de fila"
  type        = number
}

variable "sqs_alarm_period_seconds" {
  description = "Periodo em segundos para coleta de metricas dos alarmes"
  type        = number
}

variable "sqs_dlq_alarm_evaluation_periods" {
  description = "Numero de periodos para avaliar o alarme da DLQ"
  type        = number
}

variable "sqs_dlq_alarm_period_seconds" {
  description = "Periodo em segundos para coleta de metricas do alarme da DLQ"
  type        = number
}

# -----------------------------------------------------------------------------
# API Gateway Stage Configuration
# -----------------------------------------------------------------------------

variable "api_gateway_stage_name" {
  description = "Nome do stage do API Gateway (usado em metricas CloudWatch)"
  type        = string
}

variable "api_gateway_stage_throttle_burst_limit" {
  description = "Limite de burst do stage do API Gateway (requests simultaneas)"
  type        = number
}

variable "api_gateway_stage_throttle_rate_limit" {
  description = "Limite de rate do stage do API Gateway (requests por segundo)"
  type        = number
}

variable "api_gateway_integration_timeout_ms" {
  description = "Timeout em ms da integracao principal do API Gateway (authorize-purchase). Limite: 50-29000ms"
  type        = number
}

variable "api_gateway_health_check_timeout_ms" {
  description = "Timeout em ms do health check do API Gateway. Limite: 50-29000ms"
  type        = number
}

# -----------------------------------------------------------------------------
# Glue ETL Configuration
# -----------------------------------------------------------------------------

variable "glue_version" {
  description = "Versao do AWS Glue para ETL jobs"
  type        = string
}

variable "glue_worker_type" {
  description = "Tipo de worker do Glue (G.1X, G.2X, etc.)"
  type        = string
}

variable "glue_number_of_workers" {
  description = "Numero de workers para jobs Glue"
  type        = number
}

variable "glue_job_timeout" {
  description = "Timeout em minutos para jobs Glue"
  type        = number
}

variable "glue_max_retries" {
  description = "Numero maximo de retentativas para jobs Glue"
  type        = number
}

variable "glue_training_job_name" {
  description = "Nome do Glue Job de training (merge inference_logs -> transformed_zone)"
  type        = string
}

variable "glue_training_schedule" {
  description = "Schedule cron para o job de training (ex: cron(0 8 ? * SUN *))"
  type        = string
}

# -----------------------------------------------------------------------------
# DynamoDB Schema Configuration
# -----------------------------------------------------------------------------

variable "dynamodb_hash_key" {
  description = "Nome da partition key (hash key) do DynamoDB"
  type        = string
}

variable "dynamodb_range_key" {
  description = "Nome da sort key (range key) do DynamoDB"
  type        = string
}

# -----------------------------------------------------------------------------
# Data Lake S3 Prefixes
# -----------------------------------------------------------------------------

variable "s3_prefix_transformed_zone" {
  description = "Prefixo S3 para dados processados (Delta Lake)"
  type        = string
}

variable "s3_prefix_inference_logs" {
  description = "Prefixo S3 para logs de inferencia"
  type        = string
}
