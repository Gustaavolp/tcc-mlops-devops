# Modulo SQS (Simple Queue Service)

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [FIFO vs Standard](#fifo-vs-standard)
- [Dead Letter Queue](#dead-letter-queue)
- [Ciclo de Vida da Mensagem](#ciclo-de-vida-da-mensagem)
- [CloudWatch Alarms](#cloudwatch-alarms)
- [Uso](#uso)
  - [Uso Basico](#uso-basico)
  - [Uso Completo](#uso-completo)
  - [Uso para Logs/Eventos](#uso-para-logseventos)
  - [Uso com API Gateway Integration](#uso-com-api-gateway-integration)
- [Variaveis](#variaveis)
  - [Identificacao](#identificacao)
  - [Configuracao da Fila](#configuracao-da-fila)
  - [Timing](#timing)
  - [Dead Letter Queue](#dead-letter-queue-1)
  - [Criptografia](#criptografia)
  - [Monitoramento](#monitoramento)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)
- [Custos Estimados](#custos-estimados)
- [Decisoes de Arquitetura](#decisoes-de-arquitetura)
- [Referencias](#referencias)

---

## Visao Geral

| Item | Descricao |
|------|-----------|
| **Proposito** | Criar fila de mensagens para processamento assincrono de transacoes |
| **Provider** | AWS SQS |
| **Tipo** | FIFO (apenas - garante ordenacao e exactly-once) |
| **Criptografia** | SSE-SQS ou SSE-KMS |
| **Monitoramento** | CloudWatch Alarms integrados |

### Caracteristicas Principais

| Caracteristica | Descricao |
|----------------|-----------|
| **FIFO Queue** | Garante ordenacao e exactly-once processing |
| **Dead Letter Queue** | Captura mensagens que falharam apos N tentativas |
| **Content Deduplication** | Previne duplicatas baseado no hash do conteudo |
| **Long Polling** | Reduz custos e melhora latencia |
| **CloudWatch Alarms** | Alertas de acumulo, idade e falhas |
| **Serverless** | Escala automaticamente sem provisionar capacidade |

---

## Arquitetura

### Fluxo de Processamento Assincrono

```
+-----------------------------------------------------------------------------+
|                     PROCESSAMENTO ASSINCRONO DE TRANSACOES                  |
+-----------------------------------------------------------------------------+
|                                                                             |
|   PRODUTOR                        FILA                      CONSUMIDOR      |
|   ========                        ====                      ==========      |
|                                                                             |
|   +-----------+              +---------------+              +-----------+   |
|   |           |   SendMsg    |               |   ReceiveMsg |           |   |
|   |  Cliente  |------------->|   SQS FIFO    |------------->|    EKS    |   |
|   |   ELO     |              |               |              |  Worker   |   |
|   |           |              |               |              |           |   |
|   +-----------+              +-------+-------+              +-----+-----+   |
|                                      |                            |         |
|                                      |                            |         |
|                                      | Falha x3?                  | Sucesso |
|                                      v                            v         |
|                              +---------------+              +-----------+   |
|                              |               |              |           |   |
|                              |     DLQ       |              | DynamoDB  |   |
|                              | (investigar)  |              |    S3     |   |
|                              |               |              |           |   |
|                              +---------------+              +-----------+   |
|                                                                             |
+-----------------------------------------------------------------------------+

MessageGroupId = cardHolderDocument (garante ordem por cliente)
```

### Diagrama de Componentes

```
+---------------------------+
|      AWS SQS Module       |
+---------------------------+
|                           |
|  +---------------------+  |
|  |    MAIN QUEUE       |  |
|  |    (FIFO)           |  |
|  |                     |  |
|  |  - Transactions     |  |
|  |  - Ordered by Group |  |
|  |  - Exactly-once     |  |
|  +----------+----------+  |
|             |             |
|             | maxReceiveCount = 3
|             v             |
|  +---------------------+  |
|  |       DLQ           |  |
|  |   (Dead Letter)     |  |
|  |                     |  |
|  |  - Failed msgs      |  |
|  |  - 14 days retain   |  |
|  |  - Investigation    |  |
|  +---------------------+  |
|                           |
+---------------------------+
            |
            v
+---------------------------+
|   CloudWatch Alarms       |
+---------------------------+
|  - Queue Depth > 1000     |
|  - Message Age > 600s     |
|  - DLQ Not Empty          |
+---------------------------+
```

### Integracao Direta com SQS

```
                                  Cliente ELO
                                        |
                                        | SQS SendMessage (AWS SDK)
                                        |
                                        v
                            +------------------------+
                            |      SQS FIFO          |
                            |                        |
                            |  elo-fraud-            |
                            |  transactions-         |
                            |  dev.fifo              |
                            +------------------------+
                                        |
                                        | MessageGroupId: cardHolderDocument
                                        | MessageBody: transactionPayload
                                        v
                            +------------------------+
                            |     Response           |
                            |  202 Accepted          |
                            |  (asynchronous)        |
                            +------------------------+

Nota: O fluxo assincrono utiliza envio direto para SQS via AWS SDK.
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_sqs_queue.main` | Queue | Fila principal FIFO para transacoes |
| `aws_sqs_queue.dlq` | Queue | Dead Letter Queue (sempre criada) |
| `aws_cloudwatch_metric_alarm.queue_depth` | Alarm | Alerta de muitas mensagens (condicional) |
| `aws_cloudwatch_metric_alarm.message_age` | Alarm | Alerta de mensagens antigas (condicional) |
| `aws_cloudwatch_metric_alarm.dlq_not_empty` | Alarm | Alerta de falhas (condicional) |

### Convencao de Nomes

```
Este modulo cria apenas filas FIFO (sufixo .fifo obrigatorio):

  - Main Queue: {project_name}-transactions-{env}.fifo
  - DLQ:        {project_name}-transactions-dlq-{env}.fifo

Exemplos:
  - elo-fraud-transactions-dev.fifo
  - elo-fraud-transactions-dlq-dev.fifo
  - elo-fraud-transactions-prod.fifo
```

---

## FIFO vs Standard

### Comparativo

| Caracteristica | FIFO (Padrao) | Standard |
|----------------|---------------|----------|
| **Ordenacao** | Garantida por MessageGroupId | Best-effort |
| **Deduplicacao** | Exactly-once (5 min window) | At-least-once |
| **Throughput** | 300 msg/s (batch) ou 3000 msg/s (high throughput) | Ilimitado |
| **Caso de Uso** | Transacoes financeiras | Logs, eventos |
| **Sufixo** | Obrigatorio `.fifo` | Nenhum |

### Quando Usar FIFO

```
FIFO - Use quando:
+------------------------------------------+
| - Ordem das mensagens importa            |
| - Exactly-once processing e critico      |
| - Transacoes financeiras                 |
| - Operacoes que dependem de sequencia    |
+------------------------------------------+

Standard - Use quando:
+------------------------------------------+
| - Alto throughput e prioridade           |
| - Ordem nao importa                      |
| - At-least-once e aceitavel              |
| - Logs, metricas, eventos                |
+------------------------------------------+
```

### MessageGroupId

Para filas FIFO, o `MessageGroupId` agrupa mensagens que devem ser processadas em ordem:

```
MessageGroupId = "12345678900"  (CPF do cliente)

Mensagem 1 (CPF A) ----+
Mensagem 2 (CPF B) ----+-----> Processadas em paralelo (grupos diferentes)
Mensagem 3 (CPF A) ----+       Mas ordem garantida dentro do grupo

Resultado:
- CPF A: Msg 1 antes de Msg 3 (garantido)
- CPF B: Processado independentemente
```

---

## Dead Letter Queue

### Proposito

A DLQ recebe mensagens que falharam apos multiplas tentativas de processamento:

```
+------------------+     Falha      +------------------+
|   Main Queue     |--------------->|       DLQ        |
|                  |   (x3 tries)   |                  |
|  - Mensagens     |                |  - Investigacao  |
|  - Processamento |                |  - Reprocessar   |
|  - Retries       |                |  - Debug         |
+------------------+                +------------------+
```

### Configuracao

| Parametro | Valor Padrao | Descricao |
|-----------|--------------|-----------|
| `dlq_name` | (obrigatorio) | Nome da DLQ FIFO |
| `max_receive_count` | `3` | Tentativas antes de DLQ |
| `dlq_message_retention_seconds` | `1209600` (14 dias) | Retencao na DLQ |

### Beneficios

| Beneficio | Descricao |
|-----------|-----------|
| **Nao perde dados** | Mensagens falhadas sao preservadas |
| **Investigacao** | Permite debug de problemas |
| **Reprocessamento** | Mensagens podem ser devolvidas a fila principal |
| **Metricas** | Alarme dispara quando DLQ recebe mensagens |

---

## Ciclo de Vida da Mensagem

### Fluxo Normal

```
+-----------------------------------------------------------------------------+
|                        CICLO DE VIDA DA MENSAGEM                            |
+-----------------------------------------------------------------------------+
|                                                                             |
|   1. ENVIADA           2. RECEBIDA           3. PROCESSADA    4. DELETADA   |
|   +----------+        +-------------+        +------------+   +----------+  |
|   |          |        |             |        |            |   |          |  |
|   | Producer |------->| Visibility  |------->|  Consumer  |-->| Removed  |  |
|   | sends    |        | Timeout     |        |  success   |   | from     |  |
|   | message  |        | (5 min)     |        |  delete    |   | queue    |  |
|   |          |        |             |        |            |   |          |  |
|   +----------+        +------+------+        +------------+   +----------+  |
|                              |                                              |
|                              | Consumer fails / timeout                     |
|                              v                                              |
|                       +-------------+                                       |
|                       |  Returns to |                                       |
|                       |    queue    |                                       |
|                       +------+------+                                       |
|                              |                                              |
|                              | After 3 failures                             |
|                              v                                              |
|                       +-------------+                                       |
|                       |     DLQ     |                                       |
|                       | (14 days)   |                                       |
|                       +-------------+                                       |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Estados da Mensagem

| Estado | Descricao | Duracao |
|--------|-----------|---------|
| **Available** | Pronta para ser consumida | - |
| **In Flight** | Sendo processada (invisivel) | visibility_timeout |
| **Delayed** | Aguardando delay | delay_seconds |
| **Dead** | Na DLQ apos falhas | dlq_retention |

---

## CloudWatch Alarms

### Alarmes Configurados

| Alarme | Metrica | Threshold | Descricao |
|--------|---------|-----------|-----------|
| **Queue Depth** | ApproximateNumberOfMessagesVisible | > 1000 | Muitas mensagens acumuladas |
| **Message Age** | ApproximateAgeOfOldestMessage | > 600s | Mensagens antigas nao processadas |
| **DLQ Not Empty** | ApproximateNumberOfMessagesVisible (DLQ) | > 0 | Mensagens falhando |

### Diagrama de Alarmes

```
                    +------------------------+
                    |    CloudWatch Alarms   |
                    +------------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
+---------------+    +----------------+    +----------------+
| Queue Depth   |    | Message Age    |    | DLQ Not Empty  |
| > 1000 msgs   |    | > 600 seconds  |    | > 0 messages   |
+-------+-------+    +-------+--------+    +-------+--------+
        |                    |                     |
        v                    v                     v
+-------+-------+    +-------+--------+    +-------+--------+
|   INDICA:     |    |   INDICA:      |    |   INDICA:      |
| Processamento |    | Consumidor     |    | Bugs no        |
| lento/parado  |    | lento/parado   |    | processamento  |
+---------------+    +----------------+    +----------------+
```

---

## Uso

### Uso Basico

```hcl
module "sqs" {
  source = "./modules/sqs"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes das filas (obrigatorios, devem terminar com .fifo)
  queue_name = "elo-fraud-transactions-dev.fifo"
  dlq_name   = "elo-fraud-transactions-dlq-dev.fifo"

  tags = {
    Project     = "elo-fraud"
    Environment = "dev"
  }
}

# Usar a fila em outros recursos
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = module.sqs.queue_arn
  function_name    = aws_lambda_function.processor.arn
}
```

### Uso Completo

```hcl
module "sqs" {
  source = "./modules/sqs"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "prod"

  # Nomes das filas (obrigatorios, devem terminar com .fifo)
  queue_name = "elo-fraud-transactions-prod.fifo"
  dlq_name   = "elo-fraud-transactions-dlq-prod.fifo"

  # Timing
  visibility_timeout_seconds = 300      # 5 minutos para processar
  message_retention_seconds  = 1209600  # 14 dias
  delay_seconds              = 0        # Sem delay
  receive_wait_time_seconds  = 20       # Long polling maximo

  # Tamanho
  max_message_size = 262144  # 256KB

  # Dead Letter Queue
  max_receive_count             = 3
  dlq_message_retention_seconds = 1209600  # 14 dias

  # Criptografia (opcional - null usa SSE-SQS managed by AWS)
  kms_key_arn = aws_kms_key.sqs.arn

  # Monitoramento
  enable_cloudwatch_alarms    = true
  alarm_queue_depth_threshold = 1000  # Alarme se > 1000 mensagens
  alarm_age_threshold_seconds = 600   # Alarme se mensagem > 10 min
  sns_alarm_topic_arn         = aws_sns_topic.alerts.arn

  # Tags
  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    Team        = "platform"
    CostCenter  = "transactions"
  }
}

# Outputs
output "sqs_info" {
  value = {
    queue_url = module.sqs.queue_url
    queue_arn = module.sqs.queue_arn
    dlq_url   = module.sqs.dlq_url
  }
}
```

### Uso para Logs/Eventos

> **NOTA**: Este modulo cria **apenas filas FIFO**. Para filas Standard, use
> o recurso `aws_sqs_queue` diretamente.

```hcl
module "sqs_logs" {
  source = "./modules/sqs"

  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes das filas (obrigatorios, devem terminar com .fifo)
  queue_name = "elo-fraud-logs-dev.fifo"
  dlq_name   = "elo-fraud-logs-dlq-dev.fifo"

  # Timing (ajustado para logs)
  visibility_timeout_seconds = 60     # 1 minuto
  message_retention_seconds  = 86400  # 1 dia
  max_message_size           = 262144

  # DLQ
  max_receive_count = 5  # Mais tentativas para logs

  # Monitoramento
  enable_cloudwatch_alarms    = true
  alarm_queue_depth_threshold = 10000  # Threshold maior para logs

  tags = {
    Purpose = "Logging"
  }
}
```

### Uso com API Gateway Integration

```hcl
# Fila SQS
module "sqs" {
  source = "./modules/sqs"

  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes das filas (obrigatorios)
  queue_name = "elo-fraud-transactions-dev.fifo"
  dlq_name   = "elo-fraud-transactions-dlq-dev.fifo"
}

# IAM Role para API Gateway
resource "aws_iam_role" "apigw_sqs" {
  name = "elo-fraud-apigw-sqs-dev"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "apigw_sqs" {
  name = "sqs-send-message"
  role = aws_iam_role.apigw_sqs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = module.sqs.queue_arn
    }]
  })
}

# API Gateway Integration
resource "aws_apigatewayv2_integration" "sqs" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_subtype = "SQS-SendMessage"

  request_parameters = {
    "QueueUrl"       = module.sqs.queue_url
    "MessageBody"    = "$request.body"
    "MessageGroupId" = "$request.body.cardHolderDocument"
  }

  credentials_arn = aws_iam_role.apigw_sqs.arn
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `project_name` | `string` | Sim | - | Nome do projeto |
| `environment` | `string` | Sim | - | Ambiente (dev, staging, prod) |
| `tags` | `map(string)` | Nao | `{}` | Tags adicionais |

### Configuracao da Fila

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `queue_name` | `string` | Sim | - | Nome da fila SQS FIFO (deve terminar com .fifo) |
| `max_message_size` | `number` | Nao | `262144` | Tamanho maximo (1KB-256KB) |

> **NOTA:** Este modulo cria **apenas filas FIFO** (requisito do projeto para idempotencia).
> - `fifo_queue = true` (sempre)
> - `content_based_deduplication = true` (sempre)
>
> **Convencao de nomenclatura para `queue_name`:**
> ```
> {project_name}-transactions-{environment}.fifo
> ```
> Exemplos: `elo-fraud-transactions-dev.fifo`, `elo-fraud-transactions-staging.fifo`

### Timing

| Variavel | Tipo | Obrigatorio | Default | Validacao | Descricao |
|----------|------|-------------|---------|-----------|-----------|
| `visibility_timeout_seconds` | `number` | Nao | `300` | 0-43200 | Tempo de invisibilidade |
| `message_retention_seconds` | `number` | Nao | `1209600` | 60-1209600 | Retencao (max 14 dias) |
| `delay_seconds` | `number` | Nao | `0` | - | Delay antes de disponibilizar |
| `receive_wait_time_seconds` | `number` | Nao | `20` | 0-20 | Long polling timeout |

### Dead Letter Queue

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `dlq_name` | `string` | Sim | - | Nome da DLQ FIFO (deve terminar com .fifo) |
| `max_receive_count` | `number` | Nao | `3` | Tentativas antes de DLQ |
| `dlq_message_retention_seconds` | `number` | Nao | `1209600` | Retencao na DLQ |

> **NOTA**: A DLQ e **sempre criada** neste modulo para garantir que nenhuma
> mensagem seja perdida silenciosamente.

### Criptografia

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `kms_key_arn` | `string` | Nao | `null` | ARN da KMS key (null = SSE-SQS managed by AWS) |

### Monitoramento

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `enable_cloudwatch_alarms` | `bool` | Nao | `true` | Criar alarmes |
| `alarm_queue_depth_threshold` | `number` | Nao | `1000` | Threshold de mensagens |
| `alarm_age_threshold_seconds` | `number` | Nao | `600` | Threshold de idade (10 min) |
| `sns_alarm_topic_arn` | `string` | Nao | `null` | SNS topic para alarmes |

---

## Outputs

### Fila Principal

| Output | Tipo | Descricao |
|--------|------|-----------|
| `queue_id` | `string` | ID da fila SQS |
| `queue_arn` | `string` | ARN da fila SQS |
| `queue_url` | `string` | URL da fila SQS |
| `queue_name` | `string` | Nome da fila SQS |

### Dead Letter Queue

| Output | Tipo | Descricao |
|--------|------|-----------|
| `dlq_id` | `string` | ID da DLQ |
| `dlq_arn` | `string` | ARN da DLQ |
| `dlq_url` | `string` | URL da DLQ |
| `dlq_name` | `string` | Nome da DLQ |

### Configuracao

| Output | Tipo | Descricao |
|--------|------|-----------|
| `fifo_queue` | `bool` | Se e fila FIFO (sempre `true`) |
| `content_based_deduplication` | `bool` | Se usa deduplicacao baseada no conteudo (sempre `true`) |
| `visibility_timeout` | `number` | Visibility timeout em segundos |
| `max_receive_count` | `number` | Maximo de tentativas antes de DLQ |

### Alarmes

| Output | Tipo | Descricao |
|--------|------|-----------|
| `alarm_queue_depth_name` | `string` | Nome do alarme de queue depth |
| `alarm_message_age_name` | `string` | Nome do alarme de message age |
| `alarm_dlq_not_empty_name` | `string` | Nome do alarme de DLQ |

### Summary

| Output | Tipo | Descricao |
|--------|------|-----------|
| `sqs_summary` | `object` | Resumo completo da configuracao |

---

## Operacoes

### Enviar Mensagens

```bash
# Enviar mensagem para fila FIFO
aws sqs send-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --message-body '{"transaction_id": "123", "amount": 100.00}' \
  --message-group-id "12345678900" \
  --message-deduplication-id "unique-id-123"

# Enviar mensagem para fila Standard
aws sqs send-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-logs-dev" \
  --message-body '{"log": "test message"}'

# Enviar batch de mensagens
aws sqs send-message-batch \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --entries '[
    {"Id": "1", "MessageBody": "{\"tx\": 1}", "MessageGroupId": "group1"},
    {"Id": "2", "MessageBody": "{\"tx\": 2}", "MessageGroupId": "group2"}
  ]'
```

### Receber Mensagens

```bash
# Receber mensagens (long polling)
aws sqs receive-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --max-number-of-messages 10 \
  --wait-time-seconds 20

# Receber com atributos
aws sqs receive-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --attribute-names All \
  --message-attribute-names All
```

### Deletar Mensagens

```bash
# Deletar mensagem apos processamento
aws sqs delete-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --receipt-handle "AQEBwJnKy..."

# Purge - deletar todas as mensagens (CUIDADO!)
aws sqs purge-queue \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo"
```

### Ver Atributos da Fila

```bash
# Ver atributos da fila
aws sqs get-queue-attributes \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --attribute-names All \
  --output table

# Ver apenas quantidade de mensagens
aws sqs get-queue-attributes \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dev.fifo" \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible
```

### Monitorar DLQ

```bash
# Ver mensagens na DLQ (sem deletar)
aws sqs receive-message \
  --queue-url "https://sqs.sa-east-1.amazonaws.com/123456789/elo-fraud-transactions-dlq-dev.fifo" \
  --max-number-of-messages 10 \
  --visibility-timeout 0

# Mover mensagens da DLQ de volta para fila principal
# Use aws-sqs-redrive-lambda ou script customizado
```

### Ver Metricas CloudWatch

```bash
# Quantidade de mensagens
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=elo-fraud-transactions-dev.fifo \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average

# Idade da mensagem mais antiga
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateAgeOfOldestMessage \
  --dimensions Name=QueueName,Value=elo-fraud-transactions-dev.fifo \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Maximum
```

---

## Troubleshooting

### Mensagens Acumulando na Fila

**Sintoma**: Alarme `queue_depth` disparando

**Diagnostico**:
```bash
# Ver quantidade de mensagens
aws sqs get-queue-attributes \
  --queue-url "https://..." \
  --attribute-names ApproximateNumberOfMessages

# Ver idade da mensagem mais antiga
aws sqs get-queue-attributes \
  --queue-url "https://..." \
  --attribute-names ApproximateAgeOfOldestMessage
```

**Causas Comuns**:
1. Consumidor parado ou lento
2. Erro no processamento
3. Visibility timeout muito curto

**Solucoes**:
- Verificar logs do consumidor
- Escalar consumidores
- Aumentar visibility timeout se necessario

### Mensagens Indo para DLQ

**Sintoma**: Alarme `dlq_not_empty` disparando

**Diagnostico**:
```bash
# Ver mensagens na DLQ
aws sqs receive-message \
  --queue-url "https://...dlq..." \
  --visibility-timeout 0 \
  --max-number-of-messages 5
```

**Causas Comuns**:
1. Bug no codigo do consumidor
2. Payload invalido
3. Dependencia externa falhando

**Solucoes**:
- Analisar mensagens na DLQ
- Corrigir bug e reprocessar
- Verificar dependencias

### Mensagens Duplicadas (Standard Queue)

**Sintoma**: Mesma mensagem processada multiplas vezes

**Causas Comuns**:
1. Using Standard queue (at-least-once)
2. Visibility timeout muito curto
3. Consumidor nao deletando mensagem

**Solucoes**:
- Usar FIFO queue para exactly-once
- Implementar idempotencia no consumidor
- Aumentar visibility timeout

### Fila FIFO Throttling

**Sintoma**: Erro `OverLimit` ou throughput baixo

**Diagnostico**:
```bash
# Ver metricas de throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesSent \
  --dimensions Name=QueueName,Value=elo-fraud-transactions-dev.fifo \
  --period 60 \
  --statistics Sum
```

**Causas Comuns**:
1. Limite de 300 msg/s atingido
2. Muitas mensagens no mesmo MessageGroupId

**Solucoes**:
- Habilitar high throughput FIFO (3000 msg/s)
- Distribuir mensagens entre mais MessageGroupIds
- Usar batching

---

## Custos Estimados

### Precos SQS (sa-east-1)

| Tipo | Preco | Observacao |
|------|-------|------------|
| **Standard** | $0.40/milhao | Primeiros 1M gratuitos |
| **FIFO** | $0.50/milhao | Primeiros 1M gratuitos |
| **Data Transfer** | Gratuito | Dentro da mesma regiao |

### Estimativa Mensal

| Cenario | Volume | Tipo | Custo Estimado |
|---------|--------|------|----------------|
| DEV | 100K msg/mes | FIFO | ~$0 (free tier) |
| STAGING | 1M msg/mes | FIFO | ~$0.50 |
| PROD (baixo) | 10M msg/mes | FIFO | ~$5.00 |
| PROD (alto) | 100M msg/mes | FIFO | ~$50.00 |

### Otimizacao de Custos

| Tecnica | Economia | Descricao |
|---------|----------|-----------|
| **Long Polling** | ~40% | Menos chamadas vazias |
| **Batching** | ~90% | Ate 10 mensagens por request |
| **Compression** | Variavel | Payloads menores |

---

## Decisoes de Arquitetura

### Por que FIFO por Padrao?

| Decisao | FIFO Queue |
|---------|-----------|
| **Motivo** | Transacoes financeiras requerem ordem e exactly-once |
| **Beneficio** | Garante processamento correto e sem duplicatas |
| **Trade-off** | Throughput limitado (300-3000 msg/s) |
| **Alternativa** | Standard queue (para logs/eventos) |

### Por que Content-Based Deduplication?

| Decisao | Deduplicacao por Conteudo |
|---------|--------------------------|
| **Motivo** | Simplifica o produtor sem gerar IDs |
| **Beneficio** | Previne duplicatas automaticamente |
| **Trade-off** | Hash de 256KB por mensagem |
| **Alternativa** | MessageDeduplicationId explicito |

### Por que Visibility Timeout de 5 Minutos?

| Decisao | 300 segundos |
|---------|--------------|
| **Motivo** | Tempo suficiente para enriquecer e processar transacao |
| **Beneficio** | Evita reprocessamento prematuro |
| **Trade-off** | Delay maior se consumidor falhar |
| **Ajuste** | Deve ser >= tempo maximo de processamento |

### Por que Long Polling de 20 Segundos?

| Decisao | Maximo Long Polling |
|---------|---------------------|
| **Motivo** | Reduz custos e melhora latencia |
| **Beneficio** | Menos chamadas vazias, resposta imediata quando ha mensagens |
| **Trade-off** | Conexao fica aberta mais tempo |

### Por que DLQ Sempre Habilitada?

| Decisao | DLQ Obrigatoria |
|---------|-----------------|
| **Motivo** | Nunca perder mensagens silenciosamente |
| **Beneficio** | Permite investigacao e reprocessamento |
| **Trade-off** | Custo adicional minimo |
| **Alternativa** | Desabilitar apenas em casos especificos |

---

## Referencias

### AWS Documentation

- [Amazon SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/)
- [SQS FIFO Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html)
- [SQS Dead Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [SQS Message Deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html)
- [SQS Visibility Timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)

### Terraform Documentation

- [aws_sqs_queue](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue)
- [aws_cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm)

### Best Practices

- [SQS Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [Implementing Exactly-Once](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)
- [SQS and Lambda](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
