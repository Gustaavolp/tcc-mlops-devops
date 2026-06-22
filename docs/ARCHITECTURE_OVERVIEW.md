# Visao Geral da Arquitetura - Elo Fraud Detection

> **Documento Tecnico para Reuniao E2E**
> **Data**: 2026-01-16
> **Ambiente**: DEV (us-east-1)

---

## 1. Arquitetura de Alto Nivel

```
                                    FLUXO SINCRONO (p95 < 500ms)
+-------------------------------------------------------------------------------------------+
|                                                                                           |
|    +---------+      +-------------+      +-----+      +-----+      +----------+           |
|    |   Elo   | ---> | API Gateway | ---> | ALB | ---> | EKS | ---> | Response |           |
|    | Cliente |      |  (Regional) |      |     |      |     |      |          |           |
|    +---------+      +-------------+      +-----+      +-----+      +----------+           |
|                                                          |                                |
|                                            +-------------+-------------+                  |
|                                            |             |             |                  |
|                                            v             v             v                  |
|                                       +--------+   +--------+   +---------+               |
|                                       |DynamoDB|   | MLflow |   |   SQS   |               |
|                                       |(lookup)|   |(model) |   |(publish)|               |
|                                       +--------+   +--------+   +---------+               |
|                                                                      |                    |
+-------------------------------------------------------------------------------------------+
                                                                       |
                                    FLUXO ASSINCRONO                   |
+-------------------------------------------------------------------------------------------+
|                                                                      |                    |
|                                       +------------------------------+                    |
|                                       |                                                   |
|                                       v                                                   |
|                                  +----------+                                             |
|                                  | SQS FIFO |                                             |
|                                  +----------+                                             |
|                                       |                                                   |
|                                       v                                                   |
|                                  +----------+                                             |
|                                  |  Process |                                             |
|                                  |  Worker  |                                             |
|                                  +----------+                                             |
|                                       |                                                   |
|                       +---------------+---------------+                                   |
|                       |               |               |                                   |
|                       v               v               v                                   |
|                  +--------+      +--------+      +----------+                             |
|                  |DynamoDB|      |Firehose|      |CloudWatch|                             |
|                  |(update)|      |  -> S3 |      | Metrics  |                             |
|                  +--------+      +--------+      +----------+                             |
|                                       |                                                   |
|                                       v                                                   |
|                                  +----------+                                             |
|                                  |    S3    |                                             |
|                                  |Data Lake |                                             |
|                                  +----------+                                             |
|                                                                                           |
+-------------------------------------------------------------------------------------------+
```

---

## 2. Componentes AWS - Configuracao Atual

### 2.1 Tabela de Recursos

| Servico | Nome do Recurso | Regiao | Status |
|---------|-----------------|--------|--------|
| **EKS** | elo-fraud-cluster-dev | us-east-1 | ACTIVE |
| **API Gateway** | elo-fraud-api-dev (oc9dm394cf) | us-east-1 | ACTIVE |
| **ALB** | elo-fraud-alb-dev-v2 | us-east-1 | ACTIVE |
| **DynamoDB** | elo-fraud-customer-recent-tx-dev | us-east-1 | ACTIVE |
| **SQS** | elo-fraud-transactions-dev.fifo | us-east-1 | ACTIVE |
| **SQS DLQ** | elo-fraud-transactions-dlq-dev.fifo | us-east-1 | ACTIVE |
| **Firehose** | elo-fraud-transactions-firehose-dev | us-east-1 | ACTIVE |
| **Firehose** | elo-fraud-inference-firehose-dev | us-east-1 | ACTIVE |
| **S3** | elo-fraud-data-processed-dev-888577064416 | us-east-1 | ACTIVE |
| **ECR** | elo-fraud-inference-dev | us-east-1 | ACTIVE |
| **ECR** | elo-fraud-process-dev | us-east-1 | ACTIVE |

---

## 3. Configuracoes Detalhadas

### 3.1 EKS Cluster

```yaml
Nome: elo-fraud-cluster-dev
Versao Kubernetes: 1.32
Versao Plataforma: eks.30
Endpoint: https://3BBD71CED70C5D11A28B54A547DA3C64.gr7.us-east-1.eks.amazonaws.com
Node Instance Type: t3.xlarge (4 vCPU, 16GB RAM)
Nodes: 1 (min: 1, max: 3)
Namespace: fraud-detection
```

### 3.2 Pods em Execucao

| Pod | Replicas | CPU | Memory | Image |
|-----|----------|-----|--------|-------|
| inference | 2 | 500m-1000m | 512Mi-1Gi | v3.0.2-py312 |
| process | 1 | 100m-500m | 256Mi-512Mi | latest |

### 3.3 HPA (Horizontal Pod Autoscaler)

| Service | Min | Max | Current | CPU Target | Memory Target |
|---------|-----|-----|---------|------------|---------------|
| inference | 2 | 4 | 2 | 50% | 75% |
| process | 1 | 3 | 1 | 60% | 70% |

### 3.4 ALB (Application Load Balancer)

```yaml
Nome: elo-fraud-alb-dev-v2
DNS: elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com
Tipo: application
Scheme: internet-facing
Estado: active
Health Check:
  Path: /health
  Interval: 30s
  Timeout: 5s
  Healthy Threshold: 2
  Unhealthy Threshold: 3
```

### 3.5 API Gateway

```yaml
Nome: elo-fraud-api-dev
ID: oc9dm394cf
Endpoint Type: REGIONAL
Stages: dev, v1
Endpoints:
  - /health (GET)
  - /score (POST)
  - /result (POST) - deprecated
Rate Limiting:
  Burst: 5000 req
  Rate: 10000 req/s
```

### 3.6 DynamoDB

```yaml
Tabela: elo-fraud-customer-recent-tx-dev
Billing Mode: PAY_PER_REQUEST (on-demand)
Items: 4,644,101
Size: 16.4 GB
Partition Key: cardHolderDocument (String)
Sort Key: transaction_id (Number)
Encryption: AWS managed
```

### 3.7 SQS FIFO

```yaml
Queue URL: https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo
Tipo: FIFO
Visibility Timeout: 300s (5 min)
Message Retention: 14 dias
Long Polling Wait: 20s
Max Message Size: 256 KB
Content-Based Deduplication: true
DLQ:
  URL: elo-fraud-transactions-dlq-dev.fifo
  Max Receive Count: 3
```

### 3.8 Firehose Streams

| Stream | Destino S3 | Prefix | Buffer |
|--------|------------|--------|--------|
| elo-fraud-transactions-firehose-dev | elo-fraud-data-processed-dev | landing_zone/ | 1MB/60s |
| elo-fraud-inference-firehose-dev | elo-fraud-data-processed-dev | inference_logs/ | 1MB/60s |

---

## 4. Fluxo de Dados Detalhado

### 4.1 Fluxo Sincrono (Scoring)

```
1. Cliente Elo envia POST /score
   |
   v
2. API Gateway (Regional)
   - Valida payload
   - Rate limiting (10k/s)
   |
   v
3. ALB (elo-fraud-alb-dev-v2)
   - Health check dos targets
   - Distribui para pods
   |
   v
4. Inference Pod (FastAPI :8000)
   |
   +---> 4a. Normaliza payload
   |
   +---> 4b. Consulta DynamoDB (historico do usuario)
   |          - Ultimas 20 transacoes
   |          - Calcula features historicas
   |
   +---> 4c. Feature Engineering
   |          - 115+ features
   |          - Rolling windows
   |          - Lags
   |
   +---> 4d. Carrega modelo MLflow
   |          - XGBoost classifier
   |          - predict_proba()
   |
   +---> 4e. Gera score e fraud_label
   |          - score > 0.5 = fraude
   |
   +---> 4f. Publica para SQS (async)
   |
   v
5. Retorna resposta JSON
   {
     "transaction_id": "...",
     "score": 0.XX,
     "fraud_label": 0|1
   }
```

### 4.2 Fluxo Assincrono (Persistencia)

```
1. SQS FIFO recebe mensagem
   - Message Group ID: inference-logs
   - Deduplication ID: transaction_id
   |
   v
2. Process Worker (long polling 20s)
   - Batch de 10 mensagens
   |
   +---> 2a. Envia para Firehose
   |          - landing_zone/ (transaction results)
   |          - inference_logs/ (inference logs)
   |
   +---> 2b. Salva no DynamoDB
   |          - Update historico do usuario
   |          - Mantem ultimos 15 registros
   |
   +---> 2c. Publica metricas CloudWatch
   |
   v
3. Deleta mensagem do SQS
   |
   v
4. Firehose agrupa e entrega para S3
   - Buffer: 1MB ou 60s
   - Particoes Hive: year=YYYY/month=MM/day=DD/hour=HH/
```

---

## 5. Diagrama de Rede

```
                        Internet
                            |
                            v
                    +---------------+
                    | API Gateway   |
                    | (Regional)    |
                    +---------------+
                            |
                            v
+-----------------------------------------------------------------------+
|                         VPC 10.0.0.0/16                               |
|                                                                       |
|   +------------------+              +------------------+               |
|   | Public Subnet    |              | Public Subnet    |               |
|   | 10.0.1.0/24      |              | 10.0.2.0/24      |               |
|   | (us-east-1a)     |              | (us-east-1b)     |               |
|   |                  |              |                  |               |
|   |  +------------+  |              |                  |               |
|   |  |    ALB     |  |              |                  |               |
|   |  +------------+  |              |                  |               |
|   +--------|---------+              +------------------+               |
|            |                                                          |
|            v                                                          |
|   +------------------+              +------------------+               |
|   | Private Subnet   |              | Private Subnet   |               |
|   | 10.0.11.0/24     |              | 10.0.12.0/24     |               |
|   | (us-east-1a)     |              | (us-east-1b)     |               |
|   |                  |              |                  |               |
|   |                  |              |  +------------+  |               |
|   |                  |              |  | EKS Node   |  |               |
|   |                  |              |  | t3.xlarge  |  |               |
|   |                  |              |  |            |  |               |
|   |                  |              |  | inference  |  |               |
|   |                  |              |  | process    |  |               |
|   |                  |              |  +------------+  |               |
|   +------------------+              +------------------+               |
|                                                                       |
|   VPC Endpoints (Gateway - Free):                                     |
|   - S3                                                                |
|   - DynamoDB                                                          |
|                                                                       |
|   NAT Gateway: 1x (single, us-east-1a)                                |
|                                                                       |
+-----------------------------------------------------------------------+
```

---

## 6. Seguranca

### 6.1 IAM Roles

| Role | Servico | Permissoes |
|------|---------|------------|
| EKS Node Role | EKS | DynamoDB, SQS, S3, SageMaker, Firehose |
| Firehose Role | Firehose | S3 write, CloudWatch Logs |
| API Gateway Role | API Gateway | CloudWatch Logs (desabilitado) |

### 6.2 Criptografia

| Servico | Tipo | Detalhes |
|---------|------|----------|
| DynamoDB | AWS Managed | AES-256 |
| SQS | SSE-SQS | AWS Managed |
| S3 | AES-256 | Server-side |
| Firehose | AES-256 | Server-side |

### 6.3 Network Security

- ALB: Security Group permite HTTP/HTTPS
- EKS: Private subnets apenas
- VPC Endpoints: S3 e DynamoDB (trafego interno)
- NAT Gateway: Saida para internet

---

## 7. Escalabilidade

### 7.1 Auto Scaling

| Componente | Min | Max | Trigger |
|------------|-----|-----|---------|
| EKS Nodes | 1 | 3 | Cluster Autoscaler |
| Inference Pods | 2 | 4 | CPU 50%, Memory 75% |
| Process Pods | 1 | 3 | CPU 60%, Memory 70% |

### 7.2 Limites de Rate

| Servico | Limite |
|---------|--------|
| API Gateway | 10,000 req/s |
| DynamoDB | On-demand (sem limite pre-definido) |
| SQS | 3,000 msg/s (FIFO) |
| Firehose | 1,000 records/s por stream |

---

## 8. Custos Estimados (Dev)

| Servico | Configuracao | Custo/mes |
|---------|--------------|-----------|
| EKS Control Plane | 1 cluster | ~$73 |
| EC2 (t3.xlarge) | 1 node | ~$134 |
| NAT Gateway | 1x single | ~$32 |
| ALB | 1 instancia | ~$18 |
| DynamoDB | On-demand | ~$5 |
| SQS | FIFO | ~$2 |
| S3 | ~20GB | ~$5 |
| Firehose | 2 streams | ~$2 |
| **TOTAL** | | **~$270/mes** |

---

## 9. Pontos de Atencao

### 9.1 Limitacoes Conhecidas

1. **IRSA Desabilitado**: Pods usam Node IAM Role (SCP bloqueia OIDC)
2. **MLflow Stopped**: Tracking server parado, modelo carregado localmente
3. **Single NAT**: Apenas 1 NAT Gateway (nao HA para dev)
4. **Logs API GW**: Access logs desabilitados

### 9.2 SLAs

| Metrica | Target | Status |
|---------|--------|--------|
| Latencia p95 | < 500ms | Monitorar |
| Disponibilidade | 99.9% | Dependente de AWS |
| Taxa de erro | < 0.1% | Monitorar |

---

*Documento gerado em 2026-01-15*
