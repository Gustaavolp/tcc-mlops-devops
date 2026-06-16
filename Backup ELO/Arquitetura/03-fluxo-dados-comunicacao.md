# Fluxo de Dados e Comunicação - ELO Fraud Detection

**Projeto:** ELO Fraud Detection
**Ambiente:** dev
**Data:** 2025-11-23

---

## Fluxo de Requisição de Fraud Scoring (Síncrono)

Este diagrama mostra o fluxo completo de uma requisição de scoring de fraude em tempo real.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      FLUXO DE REQUISIÇÃO DE FRAUD SCORING                                       │
│                              (Processamento Síncrono)                                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   Cliente    │
     │   (VPC)      │
     │              │
     │ Envia POST   │
     │ /v1/score    │
     │ com payload  │
     └──────┬───────┘
            │
            │ 1. HTTP Request
            │    Content-Type: application/json
            │    {
            │      "transaction_id": "...",
            │      "card_hash": "...",
            │      "amount": 1000.00,
            │      ...
            │    }
            ▼
   ┌─────────────────────┐
   │   API Gateway       │
   │   (REST API)        │
   │                     │
   │ /v1/score endpoint  │
   │                     │
   │ Validations:        │
   │ - JSON Schema       │
   │ - Request model     │
   │ - Rate limiting     │
   │   (10k RPS)         │
   └──────┬──────────────┘
          │
          │ 2. HTTP Proxy Integration
          │    (Direct to ALB, no VPC Link needed)
          │
          │    Headers added:
          │    - X-Forwarded-For: source IP
          │    - X-Trace-Id: request ID
          ▼
   ┌─────────────────────┐
   │ Application Load    │
   │ Balancer (ALB)      │
   │                     │
   │ Scheme: INTERNAL    │
   │ Port: 80            │
   │                     │
   │ Health Check:       │
   │ - Path: /health     │
   │ - Interval: 30s     │
   │ - Healthy: 2 checks │
   └──────┬──────────────┘
          │
          │ 3. Route to Target Group
          │    (IP mode, direct to pod IPs)
          ▼
   ┌─────────────────────┐
   │ Kubernetes Service  │
   │ (ClusterIP)         │
   │                     │
   │ Name: inference     │
   │ Port: 8000          │
   │                     │
   │ Selector:           │
   │   app: inference    │
   └──────┬──────────────┘
          │
          │ 4. Load Balance to Pods
          │    (Round-robin across 1-4 replicas)
          ▼
   ┌─────────────────────────────────────────────────────────────────────────────────────────┐
   │ INFERENCE POD (Kubernetes)                                                              │
   │ Container: elo-fraud-inference-dev:latest                                              │
   │ Port: 8000                                                                              │
   │                                                                                         │
   │  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
   │  │ STEP 5: Enrich Request with Historical Data                                     │  │
   │  │                                                                                  │  │
   │  │ Query DynamoDB:                                                                 │  │
   │  │   Table: elo-fraud-customer-recent-tx-dev                                      │  │
   │  │   Key: card_hash = SHA256(PAN)                                                 │  │
   │  │   Query: Last 7 days transactions (TTL)                                        │  │
   │  │                                                                                  │  │
   │  │ Features extracted:                                                             │  │
   │  │   - Transaction count last 24h                                                  │  │
   │  │   - Average transaction amount                                                  │  │
   │  │   - Device changes                                                              │  │
   │  │   - Geographic patterns                                                         │  │
   │  │   - Email/phone hash matches                                                    │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │                        │ 6. DynamoDB Response                                            │
   │                        │    (Recent transactions)                                        │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 7: Call SageMaker Endpoint for ML Prediction                               │  │
   │  │                                                                                  │  │
   │  │ POST https://runtime.sagemaker.us-east-1.amazonaws.com/                        │  │
   │  │      endpoints/elo-fraud-fraud-score-dev/invocations                           │  │
   │  │                                                                                  │  │
   │  │ Request Body:                                                                   │  │
   │  │   {                                                                             │  │
   │  │     "transaction_id": "...",                                                    │  │
   │  │     "features": {                                                               │  │
   │  │       "amount": 1000.00,                                                        │  │
   │  │       "merchant_category": "...",                                               │  │
   │  │       "tx_count_24h": 5,                                                        │  │
   │  │       "avg_amount": 250.00,                                                     │  │
   │  │       ... (100+ features)                                                       │  │
   │  │     }                                                                            │  │
   │  │   }                                                                              │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │                        │ 8. SageMaker Inference                                          │
   │                        │    (ml.m6g.large, ~50-200ms)                                    │
   │                        ▼                                                                 │
   │              ┌──────────────────────┐                                                    │
   │              │ SageMaker Endpoint   │                                                    │
   │              │ fraud-score-dev      │                                                    │
   │              │                      │                                                    │
   │              │ Model: XGBoost       │                                                    │
   │              │ Instance: ml.m6g.large                                                    │
   │              │ Response:            │                                                    │
   │              │   {                  │                                                    │
   │              │     "fraud_score": 0.85,                                                  │
   │              │     "risk_level": "HIGH",                                                 │
   │              │     "decision": "DENY"                                                    │
   │              │   }                  │                                                    │
   │              └──────────┬───────────┘                                                    │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 9: Send Result to SQS (Async Processing)                                   │  │
   │  │                                                                                  │  │
   │  │ SendMessage to SQS:                                                             │  │
   │  │   Queue: fraud-detection-results-dev.fifo                                      │  │
   │  │   MessageGroupId: transaction_id                                                │  │
   │  │   MessageBody:                                                                  │  │
   │  │     {                                                                            │  │
   │  │       "transaction_id": "...",                                                   │  │
   │  │       "fraud_score": 0.85,                                                       │  │
   │  │       "risk_level": "HIGH",                                                      │  │
   │  │       "decision": "DENY",                                                        │  │
   │  │       "timestamp": "2025-11-22T10:30:00Z"                                       │  │
   │  │     }                                                                            │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 10: Return Response to Client                                              │  │
   │  │                                                                                  │  │
   │  │ HTTP 200 OK                                                                      │  │
   │  │ Content-Type: application/json                                                  │  │
   │  │                                                                                  │  │
   │  │ Response:                                                                        │  │
   │  │   {                                                                              │  │
   │  │     "transaction_id": "...",                                                     │  │
   │  │     "fraud_score": 0.85,                                                         │  │
   │  │     "risk_level": "HIGH",                                                        │  │
   │  │     "decision": "DENY",                                                          │  │
   │  │     "processing_time_ms": 180                                                    │  │
   │  │   }                                                                              │  │
   │  └──────────────────────────────────────────────────────────────────────────────────┘  │
   └─────────────────────────────────────────────────────────────────────────────────────────┘
            │
            │ 11. Response propagated back
            │     (ALB → API Gateway → Client)
            ▼
     ┌──────────────┐
     │   Cliente    │
     │   (VPC)      │
     │              │
     │ Recebe:      │
     │ - fraud_score │
     │ - decision   │
     │ - risk_level │
     └──────────────┘
```

---

## Fluxo de Processamento Assíncrono (Background Worker)

Este diagrama mostra como o worker process consome mensagens SQS e processa dados.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      FLUXO DE PROCESSAMENTO ASSÍNCRONO                                          │
│                         (Background Worker - Process Pod)                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────────────────────────┐
   │ PROCESS POD (Kubernetes Background Worker)                                             │
   │ Container: elo-fraud-process-dev:latest                                                │
   │ Continuous loop, no HTTP exposure                                                      │
   │                                                                                         │
   │  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
   │  │ STEP 1: Poll SQS Queue (Long Polling)                                           │  │
   │  │                                                                                  │  │
   │  │ ReceiveMessage from SQS:                                                        │  │
   │  │   Queue: elo-fraud-transactions-dev.fifo                                       │  │
   │  │   MaxNumberOfMessages: 10                                                       │  │
   │  │   WaitTimeSeconds: 20 (long polling)                                           │  │
   │  │   VisibilityTimeout: 300 (5 minutes to process)                                │  │
   │  │                                                                                  │  │
   │  │ Received Messages (batch):                                                      │  │
   │  │   - Message 1: transaction_data                                                 │  │
   │  │   - Message 2: transaction_data                                                 │  │
   │  │   - ...                                                                          │  │
   │  │   - Message 10: transaction_data                                                │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 2: Process Each Message (Sequentially)                                     │  │
   │  │                                                                                  │  │
   │  │ For each message:                                                               │  │
   │  │   Parse transaction data                                                        │  │
   │  │   Extract features                                                              │  │
   │  │   Validate schema                                                               │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 3: Update DynamoDB (Write Transaction History)                            │  │
   │  │                                                                                  │  │
   │  │ PutItem to DynamoDB:                                                            │  │
   │  │   Table: elo-fraud-customer-recent-tx-dev                                      │  │
   │  │   Item:                                                                          │  │
   │  │     {                                                                            │  │
   │  │       "card_hash": "SHA256(...)",                                               │  │
   │  │       "event_ts": 1700654400000,                                                │  │
   │  │       "transaction_id": "...",                                                   │  │
   │  │       "amount": 1000.00,                                                         │  │
   │  │       "merchant": "...",                                                         │  │
   │  │       "device_hash": "...",                                                      │  │
   │  │       "email_hash": "...",                                                       │  │
   │  │       "ttl": 1701259200 (7 days from now)                                       │  │
   │  │     }                                                                            │  │
   │  │                                                                                  │  │
   │  │ GSI Updates:                                                                     │  │
   │  │   - device_hash-index: Updated automatically                                    │  │
   │  │   - email_hash-index: Updated automatically                                     │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 4: Store Processed Data in S3                                              │  │
   │  │                                                                                  │  │
   │  │ PutObject to S3:                                                                │  │
   │  │   Bucket: elo-fraud-data-processed-dev                                         │  │
   │  │   Key: silver/transactions/dt=2025-11-22/txn_<transaction_id>.json            │  │
   │  │   Body:                                                                          │  │
   │  │     {                                                                            │  │
   │  │       "transaction_id": "...",                                                   │  │
   │  │       "processed_at": "2025-11-22T10:35:00Z",                                   │  │
   │  │       "enriched_features": {                                                     │  │
   │  │         "fraud_score": 0.85,                                                     │  │
   │  │         "risk_level": "HIGH",                                                    │  │
   │  │         "historical_pattern": { ... }                                           │  │
   │  │       }                                                                          │  │
   │  │     }                                                                            │  │
   │  │                                                                                  │  │
   │  │ Data Layers:                                                                     │  │
   │  │   bronze/ → Raw data (from SQS)                                                 │  │
   │  │   silver/ → Enriched data (with features)                                       │  │
   │  │   gold/   → Aggregated analytics (future)                                       │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │  ┌─────────────────────▼────────────────────────────────────────────────────────────┐  │
   │  │ STEP 5: Delete Message from SQS (Success)                                       │  │
   │  │                                                                                  │  │
   │  │ DeleteMessage from SQS:                                                         │  │
   │  │   Queue: elo-fraud-transactions-dev.fifo                                       │  │
   │  │   ReceiptHandle: <message_receipt_handle>                                       │  │
   │  │                                                                                  │  │
   │  │ On Failure (after 3 retries):                                                   │  │
   │  │   → Message moved to DLQ (elo-fraud-transactions-dlq-dev.fifo)                 │  │
   │  │   → CloudWatch Alarm triggered (DLQ not empty)                                  │  │
   │  └─────────────────────┬────────────────────────────────────────────────────────────┘  │
   │                        │                                                                 │
   │                        │ Loop back to STEP 1                                             │
   │                        │ (Continuous polling every 20s)                                  │
   │                        │                                                                 │
   └────────────────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## Fluxo Alternativo: API Gateway → SQS Direto (RFC-002)

Este diagrama mostra a integração direta do API Gateway com SQS, sem necessidade de Lambda ou ECS.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO ALTERNATIVO: API Gateway → SQS Direto                             │
│                               (RFC-002 - Direct SQS Integration)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   Cliente    │
     │   Externo    │
     │              │
     │ Envia POST   │
     │ /v1/result   │
     └──────┬───────┘
            │
            │ 1. HTTP Request
            │    POST /v1/result
            │    Body: { "transaction_id": "...", "result": "..." }
            ▼
   ┌─────────────────────┐
   │   API Gateway       │
   │   (REST API)        │
   │                     │
   │ /v1/result endpoint │
   │                     │
   │ Integration Type:   │
   │   AWS (not HTTP)    │
   └──────┬──────────────┘
          │
          │ 2. Direct AWS Integration
          │    (No Lambda, No ECS, No HTTP)
          │
          │ Request Mapping:
          │   Action=SendMessage
          │   MessageBody=$util.urlEncode($input.body)
          │   MessageGroupId=$input.json('$.transaction_id')
          │   MessageDeduplicationId=$context.requestId
          ▼
   ┌─────────────────────┐
   │   IAM Role          │
   │   API GW → SQS      │
   │                     │
   │ Permissions:        │
   │ - sqs:SendMessage   │
   │ - sqs:GetQueueUrl   │
   └──────┬──────────────┘
          │
          │ 3. Authorized SendMessage
          ▼
   ┌─────────────────────┐
   │   SQS FIFO Queue    │
   │                     │
   │ elo-fraud-          │
   │ transactions-       │
   │ dev.fifo            │
   │                     │
   │ Message Stored      │
   └──────┬──────────────┘
          │
          │ 4. Response Mapping
          │    Extract MessageId from XML
          │    Return JSON to client
          ▼
     ┌──────────────┐
     │   Cliente    │
     │              │
     │ Recebe:      │
     │ {            │
     │   "message_id": "...",
     │   "status": "queued"
     │ }            │
     └──────────────┘

   Benefícios:
   ✅ No compute costs (no Lambda/ECS middleman)
   ✅ Lower latency (direct integration)
   ✅ Higher throughput (no cold starts)
   ✅ Simpler architecture
```

---

## Métricas de Performance Esperadas

| Etapa | Latência Esperada | SLA |
|-------|-------------------|-----|
| API Gateway validação | < 10ms | p95 |
| ALB routing | < 5ms | p95 |
| DynamoDB query | < 20ms | p99 |
| SageMaker inference | 50-200ms | p95 |
| SQS send message | < 10ms | p99 |
| **Total end-to-end** | **< 300ms** | **p95** |

## SLA de Processamento Assíncrono

| Métrica | Target | Monitoramento |
|---------|--------|---------------|
| Queue depth | < 1000 msgs | CloudWatch Alarm |
| Message age | < 10 min | CloudWatch Alarm |
| DLQ depth | 0 msgs | CloudWatch Alarm |
| Processing rate | 10 msgs/20s | Custom metric |
| Success rate | > 99% | Application logs |
