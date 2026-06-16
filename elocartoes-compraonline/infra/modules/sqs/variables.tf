variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Queue Configuration (FIFO Only)
# -----------------------------------------------------------------------------
# Este modulo suporta APENAS filas FIFO para garantir:
# - Ordenacao de mensagens (First-In-First-Out)
# - Idempotencia via content_based_deduplication
# - Exatamente uma entrega (exactly-once processing)
# -----------------------------------------------------------------------------

variable "queue_name" {
  description = "Nome da fila SQS FIFO (deve terminar com .fifo)"
  type        = string

  validation {
    condition     = can(regex("\\.fifo$", var.queue_name))
    error_message = "queue_name deve terminar com .fifo (ex: elo-fraud-transactions-dev.fifo)"
  }
}

variable "fifo_queue" {
  description = "Fila FIFO - garante ordenacao e exatamente uma entrega (deve ser true)"
  type        = bool
  default     = true

  validation {
    condition     = var.fifo_queue == true
    error_message = "Este modulo suporta apenas filas FIFO. fifo_queue deve ser true."
  }
}

variable "content_based_deduplication" {
  description = "Deduplicacao baseada no conteudo da mensagem - garante idempotencia (deve ser true)"
  type        = bool
  default     = true

  validation {
    condition     = var.content_based_deduplication == true
    error_message = "Este modulo requer content_based_deduplication = true para garantir idempotencia."
  }
}

# Timing Configuration
variable "visibility_timeout_seconds" {
  description = "Tempo em segundos que mensagem fica invisível após ser recebida"
  type        = number
  default     = 300 # 5 minutos - tempo para processar

  validation {
    condition     = var.visibility_timeout_seconds >= 0 && var.visibility_timeout_seconds <= 43200
    error_message = "visibility_timeout_seconds deve estar entre 0 e 43200 (12 horas)."
  }
}

variable "message_retention_seconds" {
  description = "Tempo em segundos que mensagem fica na fila (máx 14 dias)"
  type        = number
  default     = 1209600 # 14 dias

  validation {
    condition     = var.message_retention_seconds >= 60 && var.message_retention_seconds <= 1209600
    error_message = "message_retention_seconds deve estar entre 60 e 1209600 (14 dias)."
  }
}

variable "delay_seconds" {
  description = "Tempo de delay antes da mensagem ficar disponível"
  type        = number
  default     = 0
}

variable "receive_wait_time_seconds" {
  description = "Long polling - tempo de espera por mensagens (0-20 segundos)"
  type        = number
  default     = 20 # Long polling máximo (economiza custos)

  validation {
    condition     = var.receive_wait_time_seconds >= 0 && var.receive_wait_time_seconds <= 20
    error_message = "receive_wait_time_seconds deve estar entre 0 e 20."
  }
}

# Message Size
variable "max_message_size" {
  description = "Tamanho máximo da mensagem em bytes (256KB padrão)"
  type        = number
  default     = 262144 # 256KB

  validation {
    condition     = var.max_message_size >= 1024 && var.max_message_size <= 262144
    error_message = "max_message_size deve estar entre 1024 e 262144 bytes."
  }
}

# Dead Letter Queue (DLQ)
variable "dlq_name" {
  description = "Nome da Dead Letter Queue FIFO (deve terminar com .fifo)"
  type        = string

  validation {
    condition     = can(regex("\\.fifo$", var.dlq_name))
    error_message = "dlq_name deve terminar com .fifo (ex: elo-fraud-transactions-dev-dlq.fifo)"
  }
}

variable "max_receive_count" {
  description = "Número de tentativas antes de enviar para DLQ"
  type        = number
  default     = 3
}

variable "dlq_message_retention_seconds" {
  description = "Retenção de mensagens na DLQ"
  type        = number
  default     = 1209600 # 14 dias
}

# Monitoring
variable "alarm_queue_depth_threshold" {
  description = "Threshold de mensagens para alarme (queue depth)"
  type        = number
  default     = 1000
}

variable "alarm_age_threshold_seconds" {
  description = "Threshold de idade de mensagem para alarme (segundos)"
  type        = number
  default     = 600 # 10 minutos
}

variable "dlq_alarm_threshold" {
  description = "Threshold de mensagens na DLQ para alarme (0 = qualquer mensagem)"
  type        = number
  default     = 0
}

# -----------------------------------------------------------------------------
# Alarm Timing Configuration
# -----------------------------------------------------------------------------

variable "alarm_evaluation_periods" {
  description = "Numero de periodos para avaliar os alarmes de fila"
  type        = number
  default     = 2

  validation {
    condition     = var.alarm_evaluation_periods >= 1
    error_message = "alarm_evaluation_periods deve ser pelo menos 1"
  }
}

variable "alarm_period_seconds" {
  description = "Periodo em segundos para coleta de metricas dos alarmes"
  type        = number
  default     = 300

  validation {
    condition     = contains([60, 300, 600, 900, 1800, 3600], var.alarm_period_seconds)
    error_message = "alarm_period_seconds deve ser um dos valores validos: 60, 300, 600, 900, 1800, 3600"
  }
}

variable "dlq_alarm_evaluation_periods" {
  description = "Numero de periodos para avaliar o alarme da DLQ"
  type        = number
  default     = 1

  validation {
    condition     = var.dlq_alarm_evaluation_periods >= 1
    error_message = "dlq_alarm_evaluation_periods deve ser pelo menos 1"
  }
}

variable "dlq_alarm_period_seconds" {
  description = "Periodo em segundos para coleta de metricas do alarme da DLQ"
  type        = number
  default     = 60

  validation {
    condition     = contains([60, 300, 600, 900, 1800, 3600], var.dlq_alarm_period_seconds)
    error_message = "dlq_alarm_period_seconds deve ser um dos valores validos: 60, 300, 600, 900, 1800, 3600"
  }
}
