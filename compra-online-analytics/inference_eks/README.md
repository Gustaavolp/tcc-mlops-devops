# Inference EKS - API de Detecção de Fraude

API REST em tempo real para scoring de fraude em transações 3DS usando Machine Learning.

## Visão Geral

Microsserviço FastAPI que recebe payloads de transações, realiza feature engineering, enriquece com dados históricos, executa inferência ML e retorna score de fraude em tempo real.

## Arquitetura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ POST /v1/score
       v
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌──────────────────────────┐   │
│  │  FeatureEngineering      │   │
│  │  Service                 │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  RealFeatureStore        │   │
│  │  (DynamoDB Query)        │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  ModelService            │   │
│  │  (MLflow Inference)      │   │
│  └────────┬─────────────────┘   │
│           │                     │
│           v                     │
│  ┌──────────────────────────┐   │
│  │  SQSPublisher            │   │
│  │  (Async Logging)         │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

## Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy"
}
```

### Score de Fraude
```http
POST /v1/score
Content-Type: application/json
```

**Request Body:**
```json
{
  "transaction_id": "TX123456",
  "vl_amount": "150.00",
  "nu_exponent": "2",
  "dt_transaction_datetime": "2024-01-15T14:30:00Z",
  "cardHolderDocument": "12345678900",
  "cd_merchant_country": "BR",
  "nm_browser_language": "pt-BR"
}
```

**Response:**
```json
{
  "transaction_id": "12345678",
  "score": 0.23,
  "fraud_label": 0
}
```

## Componentes

### 1. FeatureEngineeringService
Transforma payload bruto em features para o modelo.

**Responsabilidades:**
- Limpeza e normalização de valores monetários
- Parse de datas e timestamps
- Extração de features temporais (hora, dia da semana)
- Detecção de inconsistências (endereços)
- Enriquecimento com dados históricos do DynamoDB

**Arquivo:** `classes/transformer.py`

### 2. ModelService
Gerencia carregamento e inferência do modelo MLflow.

**Responsabilidades:**
- Carrega modelo do S3 via MLflow
- Executa predict_proba para probabilidades
- Converte DataFrames para formato do modelo
- Tratamento de erros de inferência

**Arquivo:** `classes/model_service.py`

### 3. RealFeatureStore
Interface com DynamoDB para features históricas.

**Responsabilidades:**
- Query de transações anteriores do usuário
- Cálculo de agregações (média, desvio, contagens)
- Features de janela temporal (últimas 10 transações)
- Detecção de padrões de fraude históricos

**Arquivo:** `classes/real_feature_store.py`

### 4. SQSPublisher
Publica eventos processados para fila SQS.

**Responsabilidades:**
- Serialização de payloads
- Envio assíncrono para SQS FIFO
- Deduplicação por transaction_id
- Logging de erros

**Arquivo:** `classes/sqs_publisher.py`

## Configuração

### Variáveis de Ambiente

```bash
# MLflow
MLFLOW_TRACKING_URI=arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ
MODEL_NAME=Felicidade

# AWS
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo

# DynamoDB
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev
```

<!-- ### Arquivo de Configuração
`inferences/config.py` -->

## Dependências

```
fastapi
uvicorn
boto3
mlflow
sagemaker
pandas
numpy
pyarrow
```

## Deploy

### Docker Build
```bash
docker build -t fraud-inference:v1.0 .
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-inference
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: <ECR>/fraud-inference:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: MLFLOW_TRACKING_URI
          value: "s3://mlflow-bucket/"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Performance

### Latência Esperada
- P50: ~150ms
- P95: ~300ms
- P99: ~500ms

### Throughput
- ~100 req/s por pod
- Escalável horizontalmente

### Otimizações
- Modelo carregado em memória no startup
- Cache de features do DynamoDB (TTL 60s)
- Publicação SQS não-bloqueante
- Connection pooling para AWS services

## Monitoramento

### Logs
```bash
kubectl logs -f deployment/fraud-inference
```

### Métricas CloudWatch
- `InferenceLatency`: Tempo de resposta
- `ModelLoadTime`: Tempo de inicialização
- `FeatureStoreLatency`: Latência DynamoDB
- `SQSPublishErrors`: Falhas de publicação

## Troubleshooting

### Modelo não carrega
```
CRITICAL: Erro fatal ao carregar modelo
```
**Solução:** Verificar IAM role, MLFLOW_TRACKING_URI e existência do modelo

### Timeout no DynamoDB
```
ERROR: Timeout ao buscar features históricas
```
**Solução:** Aumentar read capacity ou usar DAX

### Fila SQS cheia
```
ERROR: Erro SQS: ThrottlingException
```
**Solução:** Aumentar throughput da fila ou usar batching

## Testes

### Teste Local
```bash
python main.py
curl -X POST http://localhost:8000/v1/score \
  -H "Content-Type: application/json" \
  -d @payloads/payload_3ds_01.json
```

### Teste de Carga
```bash
ab -n 1000 -c 10 -p payload.json -T application/json \
  http://localhost:8000/v1/score
```

## Schema de Features

O modelo espera 80+ features incluindo:
- Valores monetários normalizados
- Features temporais (hora, dia, bins)
- Agregações históricas (média, std, percentis)
- Flags booleanas (fraude histórica, parcelamento)
- Categorias (país, idioma, banco)

Ver `classes/transformer.py` para schema completo.
