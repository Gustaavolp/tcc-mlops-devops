# Guia Completo de Testes E2E - Elo Fraud Detection

> **Autor:** Gustavo Liebl Pereira
> **Data:** 2026-01-15
> **Ambientes:** DEV (us-east-1) | STAGING (sa-east-1)

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Verificação de Saúde dos Componentes](#2-verificação-de-saúde-dos-componentes)
3. [Teste do Fluxo Síncrono (Scoring)](#3-teste-do-fluxo-síncrono-scoring)
4. [Verificação do Fluxo Assíncrono](#4-verificação-do-fluxo-assíncrono)
5. [Verificação de Métricas e Logs](#5-verificação-de-métricas-e-logs)
6. [Testes de Cenários de Fraude](#6-testes-de-cenários-de-fraude)
7. [Teste de Latência e SLA](#7-teste-de-latência-e-sla)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Pré-requisitos

### 1.1 Autenticação AWS

```bash
# Verificar perfil AWS configurado
aws --profile elo sts get-caller-identity

# Se necessário, fazer login SSO
aws sso login --profile elo
```

### 1.2 Configurar Kubeconfig

```bash
# DEV (us-east-1)
aws --profile elo --region us-east-1 eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --alias elo-dev

# STAGING (sa-east-1)
aws --profile elo --region sa-east-1 eks update-kubeconfig \
  --name elo-fraud-cluster-staging \
  --alias elo-staging

# Verificar contextos disponíveis
kubectl config get-contexts
```

### 1.3 Variáveis de Ambiente

```bash
# Configurar variáveis para facilitar os testes
export AWS_PROFILE=elo

# DEV
export DEV_REGION=us-east-1
export DEV_API_URL="https://oc9dm394cf.execute-api.us-east-1.amazonaws.com/v1"
export DEV_SQS_URL="https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo"
export DEV_DLQ_URL="https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo"
export DEV_DYNAMO_TABLE="elo-fraud-customer-recent-tx-dev"
export DEV_S3_BUCKET="elo-fraud-data-processed-dev-888577064416"
export DEV_FIREHOSE_TX="elo-fraud-transactions-firehose-dev"
export DEV_FIREHOSE_INF="elo-fraud-inference-firehose-dev"
export DEV_K8S_CONTEXT="elo-dev"

# STAGING
export STG_REGION=sa-east-1
export STG_API_URL="https://td5i6sx8rh.execute-api.sa-east-1.amazonaws.com/v1"
export STG_SQS_URL="https://sqs.sa-east-1.amazonaws.com/888577064416/elo-fraud-transactions-staging.fifo"
export STG_DLQ_URL="https://sqs.sa-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-staging.fifo"
export STG_DYNAMO_TABLE="elo-fraud-customer-recent-tx-staging"
export STG_S3_BUCKET="elo-fraud-data-processed-staging-888577064416"
export STG_FIREHOSE_TX="elo-fraud-transactions-firehose-staging"
export STG_FIREHOSE_INF="elo-fraud-inference-firehose-staging"
export STG_K8S_CONTEXT="elo-staging"
```

---

## 2. Verificação de Saúde dos Componentes

### 2.1 Health Check da API

```bash
# DEV
curl -s -w "\nStatus: %{http_code} | Tempo: %{time_total}s\n" \
  "${DEV_API_URL}/health"

# STAGING
curl -s -w "\nStatus: %{http_code} | Tempo: %{time_total}s\n" \
  "${STG_API_URL}/health"
```

### 2.2 Verificar Pods EKS

```bash
# DEV
kubectl --context $DEV_K8S_CONTEXT get pods -n fraud-detection -o wide

# STAGING
kubectl --context $STG_K8S_CONTEXT get pods -n fraud-detection -o wide

# Verificar status detalhado
kubectl --context $DEV_K8S_CONTEXT describe pods -n fraud-detection
kubectl --context $STG_K8S_CONTEXT describe pods -n fraud-detection
```

### 2.3 Verificar SQS

```bash
# DEV - Fila Principal
aws --profile $AWS_PROFILE --region $DEV_REGION sqs get-queue-attributes \
  --queue-url $DEV_SQS_URL \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# DEV - DLQ
aws --profile $AWS_PROFILE --region $DEV_REGION sqs get-queue-attributes \
  --queue-url $DEV_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages

# STAGING - Fila Principal
aws --profile $AWS_PROFILE --region $STG_REGION sqs get-queue-attributes \
  --queue-url $STG_SQS_URL \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# STAGING - DLQ
aws --profile $AWS_PROFILE --region $STG_REGION sqs get-queue-attributes \
  --queue-url $STG_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages
```

### 2.4 Verificar DynamoDB

```bash
# DEV
aws --profile $AWS_PROFILE --region $DEV_REGION dynamodb describe-table \
  --table-name $DEV_DYNAMO_TABLE \
  --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount}'

# STAGING
aws --profile $AWS_PROFILE --region $STG_REGION dynamodb describe-table \
  --table-name $STG_DYNAMO_TABLE \
  --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount}'
```

### 2.5 Verificar Firehose

```bash
# DEV - Transactions
aws --profile $AWS_PROFILE --region $DEV_REGION firehose describe-delivery-stream \
  --delivery-stream-name $DEV_FIREHOSE_TX \
  --query 'DeliveryStreamDescription.{Name:DeliveryStreamName,Status:DeliveryStreamStatus}'

# DEV - Inference
aws --profile $AWS_PROFILE --region $DEV_REGION firehose describe-delivery-stream \
  --delivery-stream-name $DEV_FIREHOSE_INF \
  --query 'DeliveryStreamDescription.{Name:DeliveryStreamName,Status:DeliveryStreamStatus}'

# STAGING - Transactions
aws --profile $AWS_PROFILE --region $STG_REGION firehose describe-delivery-stream \
  --delivery-stream-name $STG_FIREHOSE_TX \
  --query 'DeliveryStreamDescription.{Name:DeliveryStreamName,Status:DeliveryStreamStatus}'

# STAGING - Inference
aws --profile $AWS_PROFILE --region $STG_REGION firehose describe-delivery-stream \
  --delivery-stream-name $STG_FIREHOSE_INF \
  --query 'DeliveryStreamDescription.{Name:DeliveryStreamName,Status:DeliveryStreamStatus}'
```

### 2.6 Verificar S3

```bash
# DEV - Listar prefixos
aws --profile $AWS_PROFILE --region $DEV_REGION s3 ls s3://$DEV_S3_BUCKET/

# STAGING - Listar prefixos
aws --profile $AWS_PROFILE --region $STG_REGION s3 ls s3://$STG_S3_BUCKET/
```

---

## 3. Teste do Fluxo Síncrono (Scoring)

### 3.1 Payload de Teste Padrão

```bash
# Criar arquivo com payload de teste
cat > /tmp/payload_normal.json << 'EOF'
{
  "nm_payment_system_name": "Elo",
  "dt_transaction_date": "2025-03-10",
  "transaction_time": "14:30:00",
  "id_record": 1234567890,
  "nm_protocol": "2.2.0",
  "cd_device_channel": 2,
  "cd_message_category": 1,
  "cd_transaction_type": 1,
  "nu_pan_bin": 650570,
  "nu_pan_last4": 1234,
  "nm_cardholder_bill_addr_city": "São Paulo",
  "nm_cardholder_bill_addr_country": 76.0,
  "nm_cardholder_bill_addr_postal_code": "01310100",
  "nm_cardholder_bill_addr_state": "SP",
  "nm_cardholder_ship_addr_city": "São Paulo",
  "nm_cardholder_ship_addr_country": 76.0,
  "nm_cardholder_ship_addr_postal_code": "01310100",
  "nm_cardholder_ship_addr_state": "SP",
  "cd_acct_type": 2,
  "vl_amount": 15000.0,
  "nu_currency": 986,
  "vl_total": "150.00 BRL",
  "nm_merchant_name": "Magazine Luiza",
  "nm_merchant_id": 12345,
  "cd_merchant_country": 76,
  "nm_merchant_country_name": "Brazil",
  "cd_merchant_category_code": 5411,
  "nm_issuer": "Banco do Brasil SA",
  "nu_issuer_bin": 1,
  "in_browser_java_enabled": false,
  "in_browser_javascript_enabled": true,
  "nm_browser_language": "pt-BR",
  "cd_browser_time_zone": -180,
  "nm_browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
  "in_addr_match_indicator": "Y",
  "nm_message_version": "2.2.0",
  "nm_final_status": "Authenticated",
  "in_completed": "Yes",
  "nm_flow": "Frictionless",
  "flag_autorizacao": true
}
EOF
```

### 3.2 Teste de Scoring Básico

```bash
# DEV
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/payload_normal.json \
  "${DEV_API_URL}/score" | jq .

# STAGING
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/payload_normal.json \
  "${STG_API_URL}/score" | jq .
```

### 3.3 Teste com Métricas de Tempo

```bash
# DEV - Com métricas detalhadas
curl -s -w "\n---\nHTTP: %{http_code}\nTotal: %{time_total}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/payload_normal.json \
  "${DEV_API_URL}/score"

# STAGING - Com métricas detalhadas
curl -s -w "\n---\nHTTP: %{http_code}\nTotal: %{time_total}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/payload_normal.json \
  "${STG_API_URL}/score"
```

---

## 4. Verificação do Fluxo Assíncrono

### 4.1 Verificar Mensagens na SQS (Antes do Teste)

```bash
# Contar mensagens ANTES
echo "=== ANTES DO TESTE ==="

# DEV
aws --profile $AWS_PROFILE --region $DEV_REGION sqs get-queue-attributes \
  --queue-url $DEV_SQS_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' --output text

# STAGING
aws --profile $AWS_PROFILE --region $STG_REGION sqs get-queue-attributes \
  --queue-url $STG_SQS_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' --output text
```

### 4.2 Enviar Requisição de Scoring

```bash
# Gerar ID único para rastrear
export TEST_TX_ID=$(date +%s)
echo "Transaction ID de teste: $TEST_TX_ID"

# Criar payload com ID único
cat > /tmp/payload_test.json << EOF
{
  "nm_payment_system_name": "Elo",
  "dt_transaction_date": "$(date +%Y-%m-%d)",
  "transaction_time": "$(date +%H:%M:%S)",
  "id_record": $TEST_TX_ID,
  "nm_protocol": "2.2.0",
  "cd_device_channel": 2,
  "vl_amount": 25000.0,
  "nu_currency": 986,
  "nm_cardholder_bill_addr_city": "São Paulo",
  "nm_cardholder_bill_addr_country": 76.0,
  "nm_cardholder_bill_addr_state": "SP",
  "cd_merchant_country": 76,
  "cd_merchant_category_code": 5411,
  "nm_browser_language": "pt-BR",
  "cd_browser_time_zone": -180,
  "in_addr_match_indicator": "Y",
  "nm_final_status": "Authenticated",
  "flag_autorizacao": true
}
EOF

# Enviar para STAGING (modelo funcional)
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/payload_test.json \
  "${STG_API_URL}/score" | jq .
```

### 4.3 Aguardar Processamento (60-90 segundos)

```bash
# Aguardar buffer do Firehose (60s) + processamento
echo "Aguardando processamento... (90 segundos)"
sleep 90
```

### 4.4 Verificar se Mensagem foi Processada

```bash
# Verificar SQS (deve estar vazia se processou)
echo "=== SQS APÓS PROCESSAMENTO ==="
aws --profile $AWS_PROFILE --region $STG_REGION sqs get-queue-attributes \
  --queue-url $STG_SQS_URL \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# Verificar DLQ (deve estar vazia se não houve erro)
echo "=== DLQ ==="
aws --profile $AWS_PROFILE --region $STG_REGION sqs get-queue-attributes \
  --queue-url $STG_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages
```

### 4.5 Verificar DynamoDB

```bash
# Buscar registro pelo transaction_id (se salvou)
echo "=== DYNAMODB - Buscar Registro ==="
aws --profile $AWS_PROFILE --region $STG_REGION dynamodb scan \
  --table-name $STG_DYNAMO_TABLE \
  --filter-expression "transaction_id = :txid" \
  --expression-attribute-values "{\":txid\":{\"N\":\"$TEST_TX_ID\"}}" \
  --limit 1
```

### 4.6 Verificar S3 (Data Lake)

```bash
# Listar arquivos recentes no landing_zone
echo "=== S3 - Arquivos Recentes ==="
aws --profile $AWS_PROFILE --region $STG_REGION s3 ls \
  s3://$STG_S3_BUCKET/landing_zone/ --recursive | tail -10

# Baixar e visualizar último arquivo
LAST_FILE=$(aws --profile $AWS_PROFILE --region $STG_REGION s3 ls \
  s3://$STG_S3_BUCKET/landing_zone/ --recursive | tail -1 | awk '{print $4}')

echo "Último arquivo: $LAST_FILE"
aws --profile $AWS_PROFILE --region $STG_REGION s3 cp \
  s3://$STG_S3_BUCKET/$LAST_FILE /tmp/last_firehose.json

# Visualizar conteúdo
cat /tmp/last_firehose.json | jq .
```

### 4.7 Verificar Logs do Process Worker

```bash
# STAGING - Últimas 50 linhas
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/process --tail=50

# Buscar por transaction_id específico
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/process | grep "$TEST_TX_ID"
```

---

## 5. Verificação de Métricas e Logs

### 5.1 Logs do Inference Service

```bash
# DEV - Últimas 30 linhas
kubectl --context $DEV_K8S_CONTEXT logs -n fraud-detection deployment/inference --tail=30

# STAGING - Últimas 30 linhas
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/inference --tail=30

# Logs com timestamps (última hora)
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/inference --since=1h
```

### 5.2 Métricas do Firehose (CloudWatch)

```bash
# DEV - Incoming Records (última hora)
aws --profile $AWS_PROFILE --region $DEV_REGION cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=$DEV_FIREHOSE_TX \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# STAGING - Incoming Records (última hora)
aws --profile $AWS_PROFILE --region $STG_REGION cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=$STG_FIREHOSE_TX \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

### 5.3 Métricas do DynamoDB

```bash
# Consumed Read Capacity (última hora)
aws --profile $AWS_PROFILE --region $STG_REGION cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=$STG_DYNAMO_TABLE \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

### 5.4 Métricas Customizadas (EloFraud/Process)

```bash
# DEV
aws --profile $AWS_PROFILE --region $DEV_REGION cloudwatch get-metric-statistics \
  --namespace EloFraud/Process \
  --metric-name Success \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# STAGING
aws --profile $AWS_PROFILE --region $STG_REGION cloudwatch get-metric-statistics \
  --namespace EloFraud/Process \
  --metric-name Success \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

### 5.5 Eventos do Kubernetes

```bash
# DEV - Eventos recentes
kubectl --context $DEV_K8S_CONTEXT get events -n fraud-detection --sort-by='.lastTimestamp' | tail -20

# STAGING - Eventos recentes
kubectl --context $STG_K8S_CONTEXT get events -n fraud-detection --sort-by='.lastTimestamp' | tail -20
```

---

## 6. Testes de Cenários de Fraude

### 6.1 Cenário: Transação Normal (Baseline)

```bash
cat > /tmp/cenario_normal.json << 'EOF'
{
  "id_record": 100001,
  "vl_amount": 15000.0,
  "nm_cardholder_bill_addr_city": "São Paulo",
  "nm_cardholder_bill_addr_country": 76.0,
  "nm_cardholder_bill_addr_state": "SP",
  "nm_cardholder_ship_addr_city": "São Paulo",
  "nm_cardholder_ship_addr_country": 76.0,
  "nm_cardholder_ship_addr_state": "SP",
  "cd_merchant_country": 76,
  "cd_merchant_category_code": 5411,
  "nm_browser_language": "pt-BR",
  "cd_browser_time_zone": -180,
  "in_addr_match_indicator": "Y",
  "nm_final_status": "Authenticated",
  "flag_autorizacao": true
}
EOF

echo "=== CENÁRIO: Transação Normal ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d @/tmp/cenario_normal.json "${STG_API_URL}/score" | jq .
```

### 6.2 Cenário: Valor Alto (R$ 50.000)

```bash
cat > /tmp/cenario_valor_alto.json << 'EOF'
{
  "id_record": 100002,
  "vl_amount": 5000000.0,
  "nm_cardholder_bill_addr_city": "São Paulo",
  "nm_cardholder_bill_addr_country": 76.0,
  "nm_cardholder_bill_addr_state": "SP",
  "cd_merchant_country": 76,
  "cd_merchant_category_code": 5999,
  "nm_browser_language": "pt-BR",
  "cd_browser_time_zone": -180,
  "in_addr_match_indicator": "Y",
  "nm_final_status": "Authenticated",
  "flag_autorizacao": true
}
EOF

echo "=== CENÁRIO: Valor Alto R\$50.000 ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d @/tmp/cenario_valor_alto.json "${STG_API_URL}/score" | jq .
```

### 6.3 Cenário: Cross-Border (Billing Estrangeiro)

```bash
cat > /tmp/cenario_crossborder.json << 'EOF'
{
  "id_record": 100003,
  "vl_amount": 150000.0,
  "nm_cardholder_bill_addr_city": "Lagos",
  "nm_cardholder_bill_addr_country": 566.0,
  "nm_cardholder_bill_addr_state": "LA",
  "nm_cardholder_ship_addr_city": "São Paulo",
  "nm_cardholder_ship_addr_country": 76.0,
  "nm_cardholder_ship_addr_state": "SP",
  "cd_merchant_country": 76,
  "cd_merchant_category_code": 5732,
  "nm_browser_language": "en-NG",
  "cd_browser_time_zone": 60,
  "in_addr_match_indicator": "N",
  "nm_final_status": "Error ACS",
  "flag_autorizacao": false
}
EOF

echo "=== CENÁRIO: Cross-Border (Nigeria -> Brasil) ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d @/tmp/cenario_crossborder.json "${STG_API_URL}/score" | jq .
```

### 6.4 Cenário: Madrugada + Browser Russo

```bash
cat > /tmp/cenario_suspeito.json << 'EOF'
{
  "id_record": 100004,
  "transaction_time": "03:30:00",
  "vl_amount": 500000.0,
  "nm_cardholder_bill_addr_city": "São Paulo",
  "nm_cardholder_bill_addr_country": 76.0,
  "nm_cardholder_bill_addr_state": "SP",
  "cd_merchant_country": 76,
  "cd_merchant_category_code": 5999,
  "nm_browser_language": "ru-RU",
  "cd_browser_time_zone": 180,
  "in_addr_match_indicator": "N",
  "nm_final_status": "Error ACS",
  "flag_autorizacao": false
}
EOF

echo "=== CENÁRIO: Madrugada + Browser Russo ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d @/tmp/cenario_suspeito.json "${STG_API_URL}/score" | jq .
```

### 6.5 Executar Todos os Cenários

```bash
echo "=========================================="
echo "EXECUTANDO TODOS OS CENÁRIOS DE FRAUDE"
echo "=========================================="

for cenario in normal valor_alto crossborder suspeito; do
  echo ""
  echo ">>> Cenário: $cenario"
  curl -s -X POST -H "Content-Type: application/json" \
    -d @/tmp/cenario_${cenario}.json "${STG_API_URL}/score" | \
    jq '{transaction_id, score, fraud_label}'
done
```

---

## 7. Teste de Latência e SLA

### 7.1 Teste de Latência (10 Requisições)

```bash
echo "=== TESTE DE LATÊNCIA - 10 REQUISIÇÕES ==="
echo ""
echo "DEV (us-east-1):"
for i in $(seq 1 10); do
  TIME=$(curl -s -w "%{time_total}" -o /dev/null \
    -X POST -H "Content-Type: application/json" \
    -d @/tmp/payload_normal.json "${DEV_API_URL}/score")
  echo "  Req $i: ${TIME}s"
done

echo ""
echo "STAGING (sa-east-1):"
for i in $(seq 1 10); do
  TIME=$(curl -s -w "%{time_total}" -o /dev/null \
    -X POST -H "Content-Type: application/json" \
    -d @/tmp/payload_normal.json "${STG_API_URL}/score")
  echo "  Req $i: ${TIME}s"
done
```

### 7.2 Teste de Carga Leve (Paralelo)

```bash
# Instalar Apache Bench se não tiver
# sudo apt-get install apache2-utils

# Teste com 50 requisições, 5 concorrentes
echo "=== TESTE DE CARGA - 50 requisições, 5 concorrentes ==="

# Salvar payload em arquivo temporário
echo '{"id_record":999,"vl_amount":10000}' > /tmp/ab_payload.json

# DEV
ab -n 50 -c 5 -p /tmp/ab_payload.json -T "application/json" \
  "${DEV_API_URL}/score" 2>/dev/null | grep -E "Requests per second|Time per request|Percentage"

# STAGING
ab -n 50 -c 5 -p /tmp/ab_payload.json -T "application/json" \
  "${STG_API_URL}/score" 2>/dev/null | grep -E "Requests per second|Time per request|Percentage"
```

### 7.3 Script de Benchmark Completo

```bash
#!/bin/bash
# benchmark.sh - Executar múltiplas vezes para estatísticas

ENDPOINT=$1
PAYLOAD=$2
N=${3:-20}

echo "Benchmark: $N requisições para $ENDPOINT"
echo "----------------------------------------"

TIMES=()
for i in $(seq 1 $N); do
  TIME=$(curl -s -w "%{time_total}" -o /dev/null \
    -X POST -H "Content-Type: application/json" \
    -d @$PAYLOAD "$ENDPOINT")
  TIMES+=($TIME)
  echo "Req $i: ${TIME}s"
done

# Calcular estatísticas (requer bc)
echo ""
echo "--- Estatísticas ---"
echo "${TIMES[@]}" | tr ' ' '\n' | sort -n | awk '
{
  sum += $1
  data[NR] = $1
}
END {
  n = NR
  mean = sum / n
  p50 = data[int(n * 0.5)]
  p95 = data[int(n * 0.95)]
  p99 = data[int(n * 0.99)]
  printf "Min:  %.3fs\n", data[1]
  printf "Max:  %.3fs\n", data[n]
  printf "Mean: %.3fs\n", mean
  printf "p50:  %.3fs\n", p50
  printf "p95:  %.3fs\n", p95
  printf "p99:  %.3fs\n", p99
}'
```

---

## 8. Troubleshooting

### 8.1 Verificar Mensagens na DLQ

```bash
# Receber mensagem da DLQ sem deletar
aws --profile $AWS_PROFILE --region $STG_REGION sqs receive-message \
  --queue-url $STG_DLQ_URL \
  --visibility-timeout 0 \
  --max-number-of-messages 1 | jq .
```

### 8.2 Verificar Erros no Firehose

```bash
# Listar arquivos de erro
aws --profile $AWS_PROFILE --region $STG_REGION s3 ls \
  s3://$STG_S3_BUCKET/inference_logs/errors/ --recursive
```

### 8.3 Logs Detalhados dos Pods

```bash
# Inference - logs completos
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/inference --all-containers=true

# Process - logs completos com erros
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/process | grep -i "error\|exception\|fail"

# Logs em tempo real (follow)
kubectl --context $STG_K8S_CONTEXT logs -n fraud-detection deployment/process -f
```

### 8.4 Verificar Recursos dos Pods

```bash
# Top pods (CPU/Memory)
kubectl --context $STG_K8S_CONTEXT top pods -n fraud-detection

# Describe pod para ver eventos
kubectl --context $STG_K8S_CONTEXT describe pod -n fraud-detection -l app=inference

# HPA status
kubectl --context $STG_K8S_CONTEXT get hpa -n fraud-detection
kubectl --context $STG_K8S_CONTEXT describe hpa inference -n fraud-detection
```

### 8.5 Restart de Pods

```bash
# Reiniciar deployment (se necessário)
kubectl --context $STG_K8S_CONTEXT rollout restart deployment/inference -n fraud-detection
kubectl --context $STG_K8S_CONTEXT rollout restart deployment/process -n fraud-detection

# Verificar status do rollout
kubectl --context $STG_K8S_CONTEXT rollout status deployment/inference -n fraud-detection
```

### 8.6 Verificar ConfigMaps

```bash
# Ver ConfigMap do Inference
kubectl --context $STG_K8S_CONTEXT get configmap inference-config -n fraud-detection -o yaml

# Ver ConfigMap do Process
kubectl --context $STG_K8S_CONTEXT get configmap process-config -n fraud-detection -o yaml
```

---

## Checklist de Teste E2E

```
[ ] 1. Pré-requisitos configurados (AWS CLI, kubectl)
[ ] 2. Health checks passando (DEV e STAGING)
[ ] 3. Pods em estado Running
[ ] 4. Teste de scoring funcionando
[ ] 5. Score retornado corretamente
[ ] 6. Latência dentro do SLA (<500ms p95)
[ ] 7. SQS processando mensagens
[ ] 8. DLQ sem mensagens (ou investigadas)
[ ] 9. DynamoDB recebendo registros
[ ] 10. S3 landing_zone com arquivos
[ ] 11. Métricas CloudWatch disponíveis
[ ] 12. Cenários de fraude testados
```

---

*Documento gerado em 2026-01-15 para testes E2E do Elo Fraud Detection*
