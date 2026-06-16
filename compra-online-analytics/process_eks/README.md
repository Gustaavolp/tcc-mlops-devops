# Process EKS - Worker de Processamento Assíncrono

Worker Python que consome mensagens SQS, persiste dados no Data Lake (S3) e atualiza Feature Store (DynamoDB).

## Visão Geral

Microsserviço worker que processa eventos de inferência de forma assíncrona, garantindo persistência durável e atualização do feature store para enriquecimento de futuras transações.

## Arquitetura

```
┌─────────────────┐
│   SQS FIFO      │
│   Queue         │
└────────┬────────┘
         │ Long Polling (20s)
         v
┌─────────────────────────────────┐
│      Worker Process             │
│  ┌──────────────────────────┐   │
│  │  1. Receive Messages     │   │
│  │     (Batch 10)           │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  2. FirehoseClient       │   │
│  │     put_record()         │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  3. DynamoEventTable     │   │
│  │     save_event()         │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  4. Delete Message       │   │
│  │     (ACK)                │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
         │
         v
┌────────────────┐    ┌──────────────┐
│  Firehose      │    │  DynamoDB    │
│  → S3 Bucket   │    │  Table       │
└────────────────┘    └──────────────┘
```

## Componentes

### 1. Main Loop (main.py)
Loop infinito que consome e processa mensagens.

**Responsabilidades:**
- Long polling na fila SQS (20s wait time)
- Processamento em batch (até 10 mensagens)
- Tratamento de erros e retry
- Envio de métricas CloudWatch
- ACK de mensagens processadas

### 2. FirehoseClient
Interface para envio de dados ao Data Lake.

**Responsabilidades:**
- Serialização de payloads JSON
- Envio para Kinesis Firehose
- Buffering e compressão automática
- Entrega final no S3

**Arquivo:** `classes/firehose_functions.py`

### 3. DynamoEventTable
Gerenciamento do Feature Store no DynamoDB.

**Responsabilidades:**
- Persistência de eventos por usuário
- Idempotência (update se já existe)
- Rotação automática (mantém últimas 15 transações)
- Query de histórico por cardHolderDocument
- Conversão segura de tipos (Decimal, String)

**Arquivo:** `classes/dynamo_functions.py`

**Métodos principais:**
```python
save_event(card_holder_document, transaction_id, payload_dict, n_keep=15)
get_events_by_card_holder(card_holder_document)
```

## Fluxo de Processamento

### 1. Consumo SQS
```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)
```

### 2. Persistência Firehose
```python
firehose.put_record(body_dict)
# → S3: s3://bucket/year/month/day/hour/file.parquet
```

### 3. Atualização Feature Store
```python
db.save_event(
    card_holder_document=user_id,
    transaction_id=tx_id,
    payload_dict=body_dict,
    n_keep=15
)
```

### 4. ACK da Mensagem
```python
sqs.delete_message(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle
)
```

## Configuração

### Variáveis de Ambiente

```bash
# SQS
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo

# DynamoDB
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev

# Firehose
FIREHOSE_STREAM=elo-fraud-transactions-firehose-dev

# AWS
AWS_REGION=us-east-1
```

## Dependências

```
boto3
botocore
```

## Deploy

### Docker Build
```bash
docker build -t fraud-process:v1.0 .
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-process
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: worker
        image: <ECR>/fraud-process:v1.0
        env:
        - name: SQS_QUEUE_URL
          value: "https://sqs.us-east-1.amazonaws.com/..."
        - name: DYNAMO_TABLE
          value: "fraud-feature-store"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Garantias de Processamento

### Idempotência
- Mensagens duplicadas são tratadas via update no DynamoDB
- Transaction ID usado como chave de deduplicação

### Durabilidade
- Dados persistidos em S3 via Firehose (durabilidade 99.999999999%)
- DynamoDB com backups automáticos

### Rotação de Dados
- Mantém apenas últimas 15 transações por usuário
- Deleta automaticamente eventos mais antigos

### Dead Letter Queue (DLQ)
- Mensagens com falha após 3 tentativas vão para DLQ
- Reprocessamento manual via console AWS

## Monitoramento

### Logs
```bash
kubectl logs -f deployment/fraud-process
```

**Exemplos:**
```
INFO: Worker Iniciado na fila: https://sqs...
INFO: DynamoDB salvo (Via Class): User 12345678900
INFO: Success
```

### Métricas CloudWatch

**Namespace:** `EloFraud/Process`

- `Success`: Mensagens processadas com sucesso
- `DynamoSaved`: Eventos salvos no DynamoDB
- `FirehoseErrors`: Falhas no envio ao Firehose
- `SQSLag`: Mensagens pendentes na fila

### Alarmes Recomendados

```yaml
- SQS Age of Oldest Message > 5 minutos
- DynamoDB Write Throttle > 10
- Worker Pod Restarts > 3 em 10 minutos
```

## Troubleshooting

### Mensagens não são consumidas
```bash
# Verificar fila
aws sqs get-queue-attributes \
  --queue-url $SQS_QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages

# Verificar logs
kubectl logs deployment/fraud-process
```

### Erro: Float types are not supported
```
FIXED: Conversão de timestamp para Decimal no save_event()
```

### DynamoDB Throttling
```
ERROR: ProvisionedThroughputExceededException
```
**Solução:** Aumentar WCU ou habilitar auto-scaling

### Firehose Delivery Failures
```bash
# Verificar status do stream
aws firehose describe-delivery-stream \
  --delivery-stream-name $FIREHOSE_STREAM
```

## Performance

### Throughput
- ~50 mensagens/segundo por pod
- Batch de 10 mensagens por poll
- Long polling reduz chamadas vazias

### Latência
- Processamento: ~100ms por mensagem
- DynamoDB write: ~10ms
- Firehose buffer: até 60s (configurável)

### Escalabilidade
- Horizontal: Adicionar mais pods
- Vertical: Aumentar recursos do pod
- Limite: Throughput da fila SQS

## Schema DynamoDB

### Tabela: fraud-feature-store

**Chaves:**
- Partition Key: `cardHolderDocument` (String)
- Sort Key: `transaction_id` (String ou Decimal)

**Atributos:**
- `timestamp`: Decimal (Unix timestamp)
- `payload`: String (JSON serializado)

**Índices:**
- Nenhum (queries apenas por PK)

**Configuração:**
- Billing Mode: On-Demand ou Provisioned
- TTL: Opcional (90 dias)
- Point-in-time Recovery: Habilitado

## Testes

### Teste Local
```bash
# Publicar mensagem de teste
aws sqs send-message \
  --queue-url $SQS_QUEUE_URL \
  --message-body file://test_payload.json \
  --message-group-id "test" \
  --message-deduplication-id "test-123"

# Executar worker
python main.py
```

### Validação de Dados
```bash
# Verificar S3
aws s3 ls s3://bucket/fraud-transactions/

# Verificar DynamoDB
aws dynamodb query \
  --table-name fraud-feature-store \ 
  --key-condition-expression "cardHolderDocument = :doc" \
  --expression-attribute-values '{":doc":{"S":"12345678900"}}'
```

## Scripts Auxiliares

### bronze_to_silver.py
Transformação de dados brutos para formato analítico.

### silver_to_gold.py
Agregações e features para camada gold.

### gerar_bronze.ipynb
Notebook para geração de dados de teste.
