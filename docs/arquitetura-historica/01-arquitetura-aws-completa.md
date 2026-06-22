# Arquitetura AWS Completa - ELO Fraud Detection

**Ambiente:** Desenvolvimento (dev)
**AWS Account:** 888577064416
**Região:** us-east-1
**Data:** 2025-11-23

---

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS ACCOUNT: 888577064416                                       │
│                                    REGION: us-east-1                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

                                         ┌──────────────────┐
                                         │   INTERNET       │
                                         │   GATEWAY        │
                                         └────────┬─────────┘
                                                  │
┌─────────────────────────────────────────────────┼─────────────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                                │                                                 │
│ Name: elo-fraud-vpc-dev                         │                                                 │
│                                                 │                                                 │
│  ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐ │
│  │ PUBLIC SUBNETS                               │                                              │ │
│  │                                              │                                              │ │
│  │  ┌────────────────────────┐        ┌────────▼──────────────┐                              │ │
│  │  │ Public Subnet 1        │        │ Public Subnet 2       │                              │ │
│  │  │ us-east-1a             │        │ us-east-1b            │                              │ │
│  │  │ 10.0.1.0/24            │        │ 10.0.2.0/24           │                              │ │
│  │  │                        │        │                       │                              │ │
│  │  │  ┌──────────────────┐  │        │  ┌─────────────────┐  │                              │ │
│  │  │  │ Application      │  │        │  │ Application     │  │                              │ │
│  │  │  │ Load Balancer    │◄─┼────────┼─►│ Load Balancer   │  │                              │ │
│  │  │  │ (ALB)            │  │        │  │ (Target Group)  │  │                              │ │
│  │  │  │                  │  │        │  │                 │  │                              │ │
│  │  │  │ Port: 80 (HTTP)  │  │        │  │ Health: /health │  │                              │ │
│  │  │  └──────────────────┘  │        │  └─────────────────┘  │                              │ │
│  │  └────────────────────────┘        └───────────────────────┘                              │ │
│  └──────────────────────────────────────────────┬──────────────────────────────────────────────┘ │
│                                                  │                                                 │
│  ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐ │
│  │ PRIVATE SUBNETS                              │                                              │ │
│  │                                              │                                              │ │
│  │  ┌────────────────────────┐        ┌────────▼──────────────┐                              │ │
│  │  │ Private Subnet 1       │        │ Private Subnet 2      │                              │ │
│  │  │ us-east-1a             │        │ us-east-1b            │                              │ │
│  │  │ 10.0.11.0/24           │        │ 10.0.12.0/24          │                              │ │
│  │  │                        │        │                       │                              │ │
│  │  │  ┌──────────────────┐  │        │  ┌─────────────────┐  │                              │ │
│  │  │  │ EKS Node Group   │  │        │  │ EKS Node Group  │  │                              │ │
│  │  │  │ (general)        │  │        │  │ (general)       │  │                              │ │
│  │  │  │                  │  │        │  │                 │  │                              │ │
│  │  │  │ Type: t3.medium  │  │        │  │ Min: 1          │  │                              │ │
│  │  │  │ Desired: 1       │  │        │  │ Max: 3          │  │                              │ │
│  │  │  │                  │  │        │  │                 │  │                              │ │
│  │  │  │ ┌──────────────┐ │  │        │  │ ┌─────────────┐ │  │                              │ │
│  │  │  │ │ INFERENCE    │ │  │        │  │ │ PROCESS     │ │  │                              │ │
│  │  │  │ │ Pods (1-4)   │ │  │        │  │ │ Pod (1)     │ │  │                              │ │
│  │  │  │ │ Port: 8000   │ │  │        │  │ │ Background  │ │  │                              │ │
│  │  │  │ └──────────────┘ │  │        │  │ └─────────────┘ │  │                              │ │
│  │  │  └──────────────────┘  │        │  └─────────────────┘  │                              │ │
│  │  └────────────────────────┘        └───────────────────────┘                              │ │
│  │                    │                           │                                           │ │
│  │                    │                           │                                           │ │
│  └────────────────────┼───────────────────────────┼───────────────────────────────────────────┘ │
│                       │                           │                                              │
│  ┌────────────────────▼───────────────────────────▼───────────────────────────────────────────┐ │
│  │ VPC ENDPOINTS (Interface + Gateway)                                                        │ │
│  │                                                                                             │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │ │
│  │  │ S3 Gateway   │ │ DynamoDB     │ │ ECR API      │ │ ECR DKR      │ │ CloudWatch   │    │ │
│  │  │ Endpoint     │ │ Gateway      │ │ (Interface)  │ │ (Interface)  │ │ Logs (Iface) │    │ │
│  │  │              │ │ Endpoint     │ │              │ │              │ │              │    │ │
│  │  │ FREE         │ │ FREE         │ │ $7.20/month  │ │ $7.20/month  │ │ $7.20/month  │    │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │ │
│  │                                     ┌──────────────┐                                       │ │
│  │                                     │ SQS (Iface)  │                                       │ │
│  │                                     │ $7.20/month  │                                       │ │
│  │                                     └──────────────┘                                       │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                       │                           │
                       │                           │
        ┌──────────────▼─────────┐   ┌─────────────▼────────────┐
        │                        │   │                          │
┌───────▼────────┐    ┌─────────▼──────┐    ┌────────────────────▼──────────┐
│ API GATEWAY    │    │ AWS SERVICES    │    │ AWS ML SERVICES               │
│                │    │                 │    │                               │
│ REST API       │    │ ┌─────────────┐ │    │ ┌───────────────────────────┐ │
│ - /v1/score    │    │ │ S3 (4x)     │ │    │ │ SageMaker Endpoint        │ │
│ - /health      │    │ │ - raw       │ │    │ │ Name: fraud-score-dev     │ │
│ - /v1/result   │    │ │ - processed │ │    │ │ Type: ml.m6g.large        │ │
│                │    │ │ - models    │ │    │ │ Instances: 1              │ │
│ Integration:   │    │ │ - logs      │ │    │ └───────────────────────────┘ │
│ - HTTP Proxy   │    │ └─────────────┘ │    │                               │
│   to ALB       │    │                 │    │ ┌───────────────────────────┐ │
│ - Direct SQS   │    │ ┌─────────────┐ │    │ │ MLflow Tracking Server    │ │
│                │    │ │ DynamoDB    │ │    │ │ Size: Small               │ │
│ Throttling:    │    │ │             │ │    │ │ Version: 3.0              │ │
│ - Burst: 5000  │    │ │ Table:      │ │    │ │ Cost: ~$38/month          │ │
│ - Rate: 10000  │    │ │ customer-   │ │    │ └───────────────────────────┘ │
└────────────────┘    │ │ recent-tx   │ │    │                               │
                      │ │             │ │    │ ┌───────────────────────────┐ │
                      │ │ GSI: 2x     │ │    │ │ SageMaker Studio          │ │
                      │ │ - device    │ │    │ │ Type: ml.t3.medium        │ │
                      │ │ - email     │ │    │ │ Mode: PublicInternetOnly  │ │
                      │ └─────────────┘ │    │ └───────────────────────────┘ │
                      │                 │    │                               │
                      │ ┌─────────────┐ │    └───────────────────────────────┘
                      │ │ SQS (2x)    │ │
                      │ │             │ │
                      │ │ FIFO Queues:│ │
                      │ │ - txns      │ │
                      │ │ - results   │ │
                      │ │             │ │
                      │ │ DLQ: Yes    │ │
                      │ └─────────────┘ │
                      │                 │
                      │ ┌─────────────┐ │
                      │ │ ECR (3x)    │ │
                      │ │             │ │
                      │ │ Repos:      │ │
                      │ │ - inference │ │
                      │ │ - process   │ │
                      │ │ - model     │ │
                      │ └─────────────┘ │
                      └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ IAM ROLES (8 Roles)                                                                             │
│                                                                                                 │
│ 1. SageMaker Execution Role → SageMaker endpoints, S3, ECR, CloudWatch, MLflow                 │
│ 2. SageMaker Model Role → Inference endpoints, S3 read-only                                    │
│ 3. GitHub Actions OIDC Role → ECR push, EKS deploy                                             │
│ 4. Lambda Execution Role → VPC access, CloudWatch logs                                         │
│ 5. CloudWatch Events Role → EventBridge automation                                             │
│ 6. API Gateway → SQS Role → Direct SQS integration                                             │
│ 7-8. EKS IRSA Roles (commented) → inference-sa, process-sa                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes Principais

### Camada de Rede (VPC)
- **VPC CIDR:** 10.0.0.0/16
- **Subnets Públicas:** 2x (us-east-1a, us-east-1b)
- **Subnets Privadas:** 2x (us-east-1a, us-east-1b)
- **VPC Endpoints:** 7 (S3, DynamoDB, ECR, Logs, SQS)

### Camada de Computação
- **EKS Cluster:** Kubernetes 1.32
- **Node Group:** t3.medium (1-3 nodes)
- **SageMaker Endpoint:** ml.m6g.large (ARM64)

### Camada de Dados
- **S3 Buckets:** 4 (raw, processed, models, logs)
- **DynamoDB:** 1 table (customer-recent-tx-dev)
- **SQS:** 2 FIFO queues (transactions, results)
- **ECR:** 3 repositories (inference, process, model)

### Camada de ML
- **SageMaker Endpoint:** fraud-score-dev
- **MLflow Server:** Small (2 vCPU, 4GB RAM)
- **SageMaker Studio:** ml.t3.medium

### Camada de API
- **API Gateway:** REST API
- **ALB:** Application Load Balancer (interno)
- **Endpoints:** /v1/score, /health, /v1/result

---

## Recursos Provisionados

| Categoria | Recurso | Quantidade | Custo/Mês |
|-----------|---------|------------|-----------|
| Network | VPC | 1 | Free |
| Network | Subnets | 4 | Free |
| Network | VPC Endpoints (Gateway) | 2 | Free |
| Network | VPC Endpoints (Interface) | 4 | $28.80 |
| Network | ALB | 1 | $18 |
| Compute | EKS Cluster | 1 | Free |
| Compute | EKS Nodes (t3.medium) | 1-3 | $30-45 |
| Storage | S3 Buckets | 4 | $2-5 |
| Storage | DynamoDB Table | 1 | $0-2 |
| Container | ECR Repositories | 3 | $0-1 |
| Messaging | SQS FIFO Queues | 2 | $0-1 |
| ML | SageMaker Endpoint | 1 | $100-120 |
| ML | MLflow Server | 1 | $38 |
| ML | SageMaker Studio | 1 | Pay per use |
| API | API Gateway | 1 | $0-3 |
| IAM | IAM Roles | 8 | Free |
| **TOTAL** | | | **$217-283** |

---

## Observações

- **Ambiente:** Desenvolvimento (dev)
- **Multi-AZ:** Sim (us-east-1a, us-east-1b)
- **Alta Disponibilidade:** Parcial (ALB multi-AZ, EKS 1 node em dev)
- **Segurança:** VPC privada, Security Groups, IRSA pendente
- **Monitoramento:** CloudWatch Logs, métricas básicas
- **Custo otimizado:** NAT Gateway substituído por VPC Endpoints
