# Compra Online Analytics - Sistema de Detecção de Fraude

Sistema de Machine Learning para detecção de fraude em transações online, composto por dois microsserviços principais rodando em Amazon EKS.

## Arquitetura

```
┌─────────────────┐
│  Transação 3DS  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────┐
│         INFERENCE_EKS                   │
│  ┌──────────────────────────────────┐   │
│  │ 1. Feature Engineering           │   │
│  │ 2. Enriquecimento (DynamoDB)     │   │
│  │ 3. Inferência ML (MLflow)        │   │
│  │ 4. Publicação SQS                │   │
│  └──────────────────────────────────┘   │
└────────────┬────────────────────────────┘
             │
             v
      ┌─────────────┐
      │  SQS FIFO   │
      └──────┬──────┘
             │
             v
┌─────────────────────────────────────────┐
│         PROCESS_EKS (Worker)            │
│  ┌──────────────────────────────────┐   │
│  │ 1. Consumo SQS                   │   │
│  │ 2. Persistência Firehose (S3)    │   │
│  │ 3. Feature Store (DynamoDB)      │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Componentes

### 1. [Inference EKS](./inference_eks/README.md)
API de inferência em tempo real para scoring de fraude.

### 2. [Process EKS](./process_eks/README.md)
Worker assíncrono para processamento e persistência de dados.

## Tecnologias

- **Runtime**: Python 3.x
- **Orquestração**: Amazon EKS (Kubernetes)
- **ML Framework**: MLflow + SageMaker
- **API**: FastAPI
- **Mensageria**: Amazon SQS FIFO
- **Storage**: Amazon S3 (via Firehose)
- **Feature Store**: Amazon DynamoDB
- **Monitoramento**: CloudWatch

## Variáveis de Ambiente

### Inference EKS
```bash
MLFLOW_TRACKING_URI=arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ
MODEL_NAME=Felicidade
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo
AWS_REGION=us-east-1
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev
```

### Process EKS
```bash
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev
FIREHOSE_STREAM=elo-fraud-transactions-firehose-dev
AWS_REGION=us-east-1
```

## Deploy

### Pré-requisitos
- AWS CLI configurado
- kubectl configurado para o cluster EKS
- Docker instalado

### Build e Push das Imagens

```bash
# Inference
cd inference_eks
docker build -t fraud-inference:latest .
docker tag fraud-inference:latest <ECR_URI>/fraud-inference:latest
docker push <ECR_URI>/fraud-inference:latest

# Process
cd ../process_eks
docker build -t fraud-process:latest .
docker tag fraud-process:latest <ECR_URI>/fraud-process:latest
docker push <ECR_URI>/fraud-process:latest
```

### Deploy no EKS

```bash
kubectl apply -f k8s/inference-deployment.yaml
kubectl apply -f k8s/process-deployment.yaml
```

## Monitoramento

### Métricas CloudWatch

**Inference EKS:**
- Latência de inferência
- Taxa de erro
- Throughput de requisições

**Process EKS:**
- Mensagens processadas
- Erros de persistência
- Lag da fila SQS

### Health Checks

```bash
# Inference API
curl http://<INFERENCE_URL>/health

# Process Worker (logs)
kubectl logs -f deployment/fraud-process
```

## Fluxo de Dados

1. **Requisição de Score**: Cliente envia transação para `/v1/score`
2. **Feature Engineering**: Transformação e enriquecimento dos dados
3. **Inferência**: Modelo retorna probabilidade de fraude
4. **Resposta Síncrona**: Score retornado ao cliente
5. **Publicação Assíncrona**: Dados enviados para SQS
6. **Processamento**: Worker consome fila e persiste dados
7. **Data Lake**: Dados armazenados no S3 via Firehose
8. **Feature Store**: Histórico atualizado no DynamoDB

## Segurança

- IAM Roles para acesso aos serviços AWS
- Secrets Manager para credenciais sensíveis
- VPC privada para comunicação entre serviços
- Encryption at rest (S3, DynamoDB)
- Encryption in transit (TLS)

## Troubleshooting

### Inference não responde
```bash
kubectl get pods -l app=fraud-inference
kubectl logs <pod-name>
```

### Process não consome mensagens
```bash
# Verificar visibilidade da fila
aws sqs get-queue-attributes --queue-url <URL> --attribute-names ApproximateNumberOfMessages

# Logs do worker
kubectl logs -f deployment/fraud-process
```

### Modelo não carrega
- Verificar permissões IAM para S3
- Validar MLFLOW_TRACKING_URI
- Confirmar existência do modelo registrado

## Licença

Proprietary - Uso interno apenas
