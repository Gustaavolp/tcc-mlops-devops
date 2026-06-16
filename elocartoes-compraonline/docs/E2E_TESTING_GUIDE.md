# Guia de Testes End-to-End - Elo Fraud Detection

> **Documento para reuniao de testes E2E**
> **Data**: 2026-01-16
> **Ambiente**: DEV (us-east-1)
> **Responsavel DevOps**: Gustavo Liebl Pereira

---

## 1. Resumo Executivo

Este documento descreve os procedimentos para execucao de testes end-to-end na plataforma de deteccao de fraudes da Elo. O sistema processa transacoes 3DS em tempo real e retorna um score de fraude com **SLA de p95 < 500ms**.

### 1.1 Status Atual da Infraestrutura (Verificado em 2026-01-15)

| Componente | Status | Detalhes |
|------------|--------|----------|
| EKS Cluster | **ACTIVE** | v1.32, platform eks.30 |
| Inference Pods | **Running** | 2/2 replicas |
| Process Pod | **Running** | 1/1 replica |
| ALB | **Active** | internet-facing |
| API Gateway | **Active** | Stage v1 |
| DynamoDB | **Active** | 4.6M items, 16.4GB |
| SQS FIFO | **Active** | 0 mensagens pendentes |
| Firehose (2 streams) | **Active** | Entregando para S3 |

---

## 2. Endpoints de Teste

### 2.1 URLs Disponiveis

```
# Via ALB (direto para EKS)
ALB_URL=http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com

# Via API Gateway
API_GW_URL=https://oc9dm394cf.execute-api.us-east-1.amazonaws.com/v1
```

### 2.2 Endpoints

| Endpoint | Metodo | Descricao | Autenticacao |
|----------|--------|-----------|--------------|
| `/health` | GET | Health check | Nenhuma |
| `/score` | POST | Scoring de fraude | API Key (opcional em dev) |

---

## 3. Testes Rapidos de Validacao

### 3.1 Health Check

```bash
# Via ALB (recomendado para testes)
curl -s http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health

# Via API Gateway
curl -s https://oc9dm394cf.execute-api.us-east-1.amazonaws.com/v1/health
```

**Resposta esperada:**
```json
{"status": "healthy"}
```

### 3.2 Teste de Scoring Basico

```bash
# Payload minimo para teste
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST-001",
    "cardHolderDocument": "12345678901",
    "amount": "150.00",
    "cd_merchant_category_code": "5411",
    "cd_merchant_country": "BRA"
  }'
```

**Resposta esperada:**
```json
{
  "transaction_id": "TEST-001",
  "score": 0.23,
  "fraud_label": 0
}
```

---

## 4. Passo a Passo: Teste End-to-End Completo

### 4.1 Pre-requisitos

```bash
# 1. Configurar AWS CLI (se nao configurado)
aws configure --profile elo

# 2. Configurar kubectl para EKS
aws --profile elo eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --region us-east-1

# 3. Verificar conectividade
kubectl get pods -n fraud-detection
```

### 4.2 Etapa 1: Verificar Saude do Sistema

```bash
# Verificar pods
kubectl get pods -n fraud-detection -o wide

# Verificar HPA
kubectl get hpa -n fraud-detection

# Verificar health endpoint
curl -s http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/health | jq .
```

### 4.3 Etapa 2: Enviar Transacao de Teste

```bash
# Criar payload de teste completo (salvar como test_payload.json)
cat > /tmp/test_payload.json << 'EOF'
{
  "transaction_id": "E2E-TEST-$(date +%s)",
  "cardHolderDocument": "12345678901",
  "amount": "299.90",
  "cd_merchant_category_code": "5411",
  "cd_merchant_country": "BRA",
  "nm_merchant_country_name": "Brazil",
  "cd_device_channel": "02",
  "cd_browser_time_zone": "-180",
  "nm_browser_language": "pt-BR",
  "enr_device_os": "Windows",
  "nm_cardholder_bill_addr_state": "SP",
  "nm_cardholder_bill_addr_country": "BR",
  "nm_protocol": "2.2.0",
  "cd_transaction_status": "Y",
  "cd_eci": "05"
}
EOF

# Enviar request e medir tempo
time curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d @/tmp/test_payload.json \
  -w "\n\nTempo Total: %{time_total}s\nTempo Conexao: %{time_connect}s\nTempo TTFB: %{time_starttransfer}s\n"
```

### 4.4 Etapa 3: Validar Fluxo Assincrono

```bash
# 1. Verificar se mensagem foi enviada para SQS (deve estar 0 se process consumiu)
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1

# 2. Verificar logs do process worker
kubectl logs -n fraud-detection deployment/process --tail=20

# 3. Verificar DLQ (deve estar vazia)
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1
```

### 4.5 Etapa 4: Verificar Persistencia

```bash
# Verificar item no DynamoDB
aws --profile elo dynamodb query \
  --table-name elo-fraud-customer-recent-tx-dev \
  --key-condition-expression "cardHolderDocument = :doc" \
  --expression-attribute-values '{":doc": {"S": "12345678901"}}' \
  --limit 1 \
  --region us-east-1

# Verificar dados no S3 (Firehose)
aws --profile elo s3 ls s3://elo-fraud-data-processed-dev-888577064416/landing_zone/ --recursive | tail -5
```

---

## 5. Medicao de Performance

### 5.1 Script de Medicao de Latencia

```bash
#!/bin/bash
# Salvar como: test_latency.sh

URL="http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score"
PAYLOAD='{"transaction_id":"PERF-TEST","cardHolderDocument":"99999999999","amount":"100.00","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}'

echo "=== Teste de Latencia (10 requests) ==="
echo ""

total_time=0
for i in {1..10}; do
  response_time=$(curl -s -o /dev/null -w "%{time_total}" -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  time_ms=$(echo "$response_time * 1000" | bc)
  total_time=$(echo "$total_time + $time_ms" | bc)
  printf "Request %2d: %6.2f ms\n" $i $time_ms
done

avg_time=$(echo "scale=2; $total_time / 10" | bc)
echo ""
echo "=== Resultado ==="
echo "Media: ${avg_time} ms"
echo "SLA (p95 < 500ms): $([ $(echo "$avg_time < 500" | bc) -eq 1 ] && echo 'OK' || echo 'FALHOU')"
```

### 5.2 Executar Teste de Latencia

```bash
chmod +x test_latency.sh
./test_latency.sh
```

### 5.3 Teste de Carga Simples (usando curl em paralelo)

```bash
# Teste de carga simples: 50 requests paralelos
seq 50 | xargs -P 10 -I {} curl -s -o /dev/null -w "Request {}: %{time_total}s\n" \
  -X POST http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"LOAD-{}","cardHolderDocument":"11111111111","amount":"50.00","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}'
```

---

## 6. Cenarios de Teste

### 6.1 Cenario 1: Transacao Normal (Baixo Risco)

```json
{
  "transaction_id": "NORMAL-001",
  "cardHolderDocument": "12345678901",
  "amount": "89.90",
  "cd_merchant_category_code": "5411",
  "cd_merchant_country": "BRA",
  "nm_merchant_country_name": "Brazil",
  "cd_device_channel": "02",
  "enr_device_os": "Android",
  "nm_cardholder_bill_addr_state": "SP",
  "nm_cardholder_bill_addr_country": "BR",
  "nm_protocol": "2.2.0",
  "cd_transaction_status": "Y"
}
```
**Resultado esperado:** `score < 0.3`, `fraud_label: 0`

### 6.2 Cenario 2: Transacao Suspeita (Alto Valor)

```json
{
  "transaction_id": "SUSPECT-001",
  "cardHolderDocument": "98765432109",
  "amount": "15000.00",
  "cd_merchant_category_code": "5944",
  "cd_merchant_country": "USA",
  "nm_merchant_country_name": "United States",
  "cd_device_channel": "01",
  "enr_device_os": "iOS",
  "nm_cardholder_bill_addr_state": "NY",
  "nm_cardholder_bill_addr_country": "US",
  "nm_protocol": "2.2.0",
  "cd_transaction_status": "A"
}
```
**Resultado esperado:** `score > 0.5`, `fraud_label: 1`

### 6.3 Cenario 3: Transacao Internacional

```json
{
  "transaction_id": "INTL-001",
  "cardHolderDocument": "55544433322",
  "amount": "500.00",
  "cd_merchant_category_code": "5812",
  "cd_merchant_country": "PRT",
  "nm_merchant_country_name": "Portugal",
  "cd_device_channel": "02",
  "enr_device_os": "Windows",
  "nm_cardholder_bill_addr_state": "Lisboa",
  "nm_cardholder_bill_addr_country": "PT"
}
```

---

## 7. Checklist de Validacao E2E

### 7.1 Fluxo Sincrono

- [ ] Health check retorna 200
- [ ] Endpoint /score aceita POST
- [ ] Resposta contem `transaction_id`, `score`, `fraud_label`
- [ ] Tempo de resposta < 500ms (p95)
- [ ] Score esta entre 0 e 1
- [ ] fraud_label e 0 ou 1

### 7.2 Fluxo Assincrono

- [ ] Mensagem enviada para SQS
- [ ] Process worker consome mensagem
- [ ] Item salvo no DynamoDB
- [ ] Dados enviados para Firehose
- [ ] Dados chegam no S3 (landing_zone/)
- [ ] DLQ vazia (sem erros)

### 7.3 Observabilidade

- [ ] Logs do inference acessiveis
- [ ] Logs do process acessiveis
- [ ] Metricas do HPA funcionando
- [ ] CloudWatch recebendo metricas

---

## 8. Comandos Uteis para a Reuniao

```bash
# === MONITORAMENTO EM TEMPO REAL ===

# Watch pods
watch -n 2 kubectl get pods -n fraud-detection

# Watch HPA
watch -n 5 kubectl get hpa -n fraud-detection

# Logs em tempo real (inference)
kubectl logs -f -n fraud-detection deployment/inference

# Logs em tempo real (process)
kubectl logs -f -n fraud-detection deployment/process

# === METRICAS AWS ===

# SQS depth
aws --profile elo sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo \
  --attribute-names ApproximateNumberOfMessages --region us-east-1

# DynamoDB item count
aws --profile elo dynamodb describe-table \
  --table-name elo-fraud-customer-recent-tx-dev \
  --query 'Table.ItemCount' --region us-east-1

# === TROUBLESHOOTING ===

# Descrever pod com problema
kubectl describe pod -n fraud-detection <POD_NAME>

# Ver eventos do namespace
kubectl get events -n fraud-detection --sort-by='.lastTimestamp'

# Restart deployment
kubectl rollout restart deployment/inference -n fraud-detection
```

---

## 9. Contatos e Suporte

| Area | Responsavel | Contato |
|------|-------------|---------|
| DevOps/Infra | Gustavo Liebl Pereira | - |
| ML/Data Science | Ana/Vinicios | - |
| Dados 3DS | Denis | - |

---

*Documento gerado em 2026-01-15 para reuniao de testes E2E*
