# Dependências Terraform - ELO Fraud Detection

**Projeto:** ELO Fraud Detection
**Total de Módulos:** 12
**Total de Recursos AWS:** 30+
**Data:** 2025-11-23

---

## Grafo de Dependências entre Módulos

Este diagrama mostra as dependências entre todos os módulos Terraform e a ordem recomendada de deployment.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        TERRAFORM MODULES DEPENDENCY GRAPH                                       │
│                            (12 Modules, 30+ AWS Resources)                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

LAYER 1: FOUNDATION (No dependencies)
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ MODULE: vpc                                                                          │   │
│   │ Path: infra/modules/vpc/                                                             │   │
│   │                                                                                      │   │
│   │ Creates:                                                                             │   │
│   │   • aws_vpc (10.0.0.0/16)                                                            │   │
│   │   • 2x Public Subnets (us-east-1a, us-east-1b)                                      │   │
│   │   • 2x Private Subnets (us-east-1a, us-east-1b)                                     │   │
│   │   • Internet Gateway                                                                 │   │
│   │   • Route Tables (public, private)                                                   │   │
│   │   • Security Groups (ALB, VPC Endpoints)                                            │   │
│   │   • 7x VPC Endpoints (S3, DDB, ECR, Logs, SQS)                                      │   │
│   │                                                                                      │   │
│   │ Outputs:                                                                             │   │
│   │   • vpc_id                      → Used by: ALB, EKS, S3 endpoints                  │   │
│   │   • public_subnet_ids           → Used by: ALB                                      │   │
│   │   • private_subnet_ids          → Used by: EKS                                      │   │
│   │   • sg_alb_id                   → Used by: ALB                                      │   │
│   │   • vpc_endpoint_s3_id          → Used by: S3 route table associations             │   │
│   │   • vpc_endpoint_dynamodb_id    → Used by: DynamoDB route table associations       │   │
│   └──────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
         │                           │                          │
         │                           │                          │
         ▼                           ▼                          ▼

LAYER 2: STORAGE & DATA (Depends on VPC for endpoints)
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐                  │
│   │ MODULE: s3          │   │ MODULE: dynamodb    │   │ MODULE: sqs      │                  │
│   │                     │   │                     │   │                  │                  │
│   │ Creates:            │   │ Creates:            │   │ Creates:         │                  │
│   │ • 4x S3 Buckets:    │   │ • DDB Table         │   │ • FIFO Queue     │                  │
│   │   - raw             │   │   (customer-recent  │   │ • DLQ            │                  │
│   │   - processed       │   │    -tx-dev)         │   │ • 3x Alarms      │                  │
│   │   - models          │   │ • 2x GSI            │   │                  │                  │
│   │   - logs            │   │   (device, email)   │   │ Properties:      │                  │
│   │ • Lifecycle rules   │   │ • TTL config        │   │ • Content dedupe │                  │
│   │ • Versioning        │   │                     │   │ • Retention 14d  │                  │
│   │ • Encryption        │   │ Billing:            │   │ • Visibility 5m  │                  │
│   │                     │   │ PAY_PER_REQUEST     │   │                  │                  │
│   │ Outputs:            │   │                     │   │ Outputs:         │                  │
│   │ • bucket_arns[4]    │   │ Outputs:            │   │ • queue_arn      │                  │
│   │ • bucket_names[4]   │   │ • table_arn         │   │ • queue_url      │                  │
│   └──────┬──────────────┘   └──────┬──────────────┘   │ • dlq_arn        │                  │
│          │                         │                  └────┬─────────────┘                  │
│          │                         │                       │                                 │
│   ┌──────▼──────────────┐   ┌──────────────────────┐      │                                 │
│   │ MODULE: ecr         │   │ MODULE: mlflow       │      │                                 │
│   │                     │   │                      │      │                                 │
│   │ Creates:            │   │ Creates:             │      │                                 │
│   │ • 3x ECR Repos:     │   │ • MLflow Server      │      │                                 │
│   │   - inference-dev   │   │   (SageMaker)        │      │                                 │
│   │   - process-dev     │   │ • Artifacts Bucket   │      │                                 │
│   │   - model-dev       │   │ • Execution Role     │      │                                 │
│   │ • Lifecycle policy  │   │                      │      │                                 │
│   │ • Image scanning    │   │ Size: Small          │      │                                 │
│   │                     │   │ Cost: ~$38/month     │      │                                 │
│   │ Outputs:            │   │                      │      │                                 │
│   │ • repo_urls[3]      │   │ Outputs:             │      │                                 │
│   │ • repo_arns[3]      │   │ • tracking_server_arn│      │                                 │
│   └─────────────────────┘   │ • artifact_bucket    │      │                                 │
│                             └──────────────────────┘      │                                 │
└───────────────────────────────────────────────────────────┼─────────────────────────────────┘
         │                           │                       │
         │                           │                       │
         ▼                           ▼                       ▼

LAYER 3: IAM & SECURITY (Depends on S3, DynamoDB, SQS, ECR)
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ MODULE: iam                                                                          │   │
│   │                                                                                      │   │
│   │ Creates 8 IAM Roles:                                                                 │   │
│   │                                                                                      │   │
│   │ 1. SageMaker Execution Role                                                          │   │
│   │    • Trusts: sagemaker.amazonaws.com                                                │   │
│   │    • Policies: S3 (all buckets), ECR (pull), CloudWatch, MLflow                    │   │
│   │    • Used by: SageMaker endpoints, MLflow                                           │   │
│   │                                                                                      │   │
│   │ 2. SageMaker Model Role                                                              │   │
│   │    • Trusts: sagemaker.amazonaws.com                                                │   │
│   │    • Policies: S3 (models bucket read-only), CloudWatch                            │   │
│   │    • Used by: SageMaker inference endpoints                                         │   │
│   │                                                                                      │   │
│   │ 3. GitHub Actions OIDC Role                                                          │   │
│   │    • Trusts: token.actions.githubusercontent.com                                    │   │
│   │    • Condition: repo:cristovamperes-compasso/elocartoes-compraonline:*             │   │
│   │    • Policies: ECR (push), EKS (describe), S3 (artifacts)                          │   │
│   │    • Used by: CI/CD pipeline                                                         │   │
│   │                                                                                      │   │
│   │ 4. Lambda Execution Role                                                             │   │
│   │    • Trusts: lambda.amazonaws.com                                                   │   │
│   │    • Policies: VPC access, CloudWatch logs                                          │   │
│   │                                                                                      │   │
│   │ 5. CloudWatch Events Role                                                            │   │
│   │    • Trusts: events.amazonaws.com                                                   │   │
│   │    • Used by: EventBridge automation                                                │   │
│   │                                                                                      │   │
│   │ 6. API Gateway → SQS Role                                                            │   │
│   │    • Trusts: apigateway.amazonaws.com                                               │   │
│   │    • Policies: sqs:SendMessage, sqs:GetQueueUrl                                     │   │
│   │    • Used by: /v1/result endpoint (direct SQS integration)                          │   │
│   │                                                                                      │   │
│   │ 7-8. EKS IRSA Roles (COMMENTED - future)                                            │   │
│   │    • eks_inference_role (for inference pods)                                        │   │
│   │    • eks_process_role (for process pods)                                            │   │
│   │    • Requires: EKS OIDC provider ARN                                                │   │
│   │                                                                                      │   │
│   │ Inputs:                                                                              │   │
│   │   • s3_bucket_arns (from s3 module)                                                 │   │
│   │   • dynamodb_table_arn (from dynamodb module)                                       │   │
│   │   • sqs_queue_arns (from sqs module)                                                │   │
│   │   • ecr_repository_arns (from ecr module)                                           │   │
│   │                                                                                      │   │
│   │ Outputs:                                                                             │   │
│   │   • sagemaker_execution_role_arn    → Used by: SageMaker, MLflow                   │   │
│   │   • sagemaker_model_role_arn        → Used by: SageMaker endpoint                  │   │
│   │   • github_actions_role_arn         → Used by: GitHub Actions workflows            │   │
│   │   • api_gateway_sqs_role_arn        → Used by: API Gateway                         │   │
│   └──────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
         │                           │                          │
         │                           │                          │
         ▼                           ▼                          ▼

LAYER 4: COMPUTE & NETWORKING (Depends on VPC, IAM)
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐                  │
│   │ MODULE: alb         │   │ MODULE: eks         │   │ MODULE: api-gw   │                  │
│   │                     │   │                     │   │                  │                  │
│   │ Creates:            │   │ Creates:            │   │ Creates:         │                  │
│   │ • ALB               │   │ • EKS Cluster 1.32  │   │ • REST API       │                  │
│   │ • Target Group      │   │ • OIDC Provider     │   │ • Resources:     │                  │
│   │ • Listener HTTP:80  │   │ • Managed Node Grp  │   │   /v1/score      │                  │
│   │ • Health check      │   │   - t3.medium       │   │   /health        │                  │
│   │                     │   │   - Min: 1, Max: 3  │   │   /v1/result     │                  │
│   │ Scheme: Internet    │   │   - Desired: 1      │   │                  │                  │
│   │ Idle timeout: 60s   │   │ • Addons:           │   │ Integrations:    │                  │
│   │                     │   │   - coredns         │   │ • HTTP Proxy     │                  │
│   │ Inputs:             │   │   - kube-proxy      │   │   to ALB         │                  │
│   │ • vpc_id            │   │   - vpc-cni         │   │ • Direct SQS     │                  │
│   │ • public_subnets    │   │                     │   │   (RFC-002)      │                  │
│   │ • sg_alb_id         │   │ Logging:            │   │                  │                  │
│   │                     │   │ • api, audit        │   │ Throttling:      │                  │
│   │ Outputs:            │   │                     │   │ • Burst: 5000    │                  │
│   │ • alb_dns_name      │   │ Inputs:             │   │ • Rate: 10000    │                  │
│   │ • alb_arn           │   │ • vpc_id            │   │                  │                  │
│   │ • target_group_arn  │   │ • private_subnets   │   │ Inputs:          │                  │
│   └──────┬──────────────┘   │                     │   │ • alb_dns_name   │                  │
│          │                  │ Outputs:            │   │ • sqs_queue_arn  │                  │
│          │                  │ • cluster_name      │   │ • api_gw_sqs_role│                  │
│          │                  │ • cluster_endpoint  │   │                  │                  │
│          │                  │ • oidc_provider_arn │   │ Outputs:         │                  │
│          │                  └─────────────────────┘   │ • api_endpoint   │                  │
│          │                                            │ • api_id         │                  │
│          │                                            └──────────────────┘                  │
│          │                                                                                   │
│          └─────────────────────► Used by API Gateway (HTTP Proxy integration)               │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
         │                           │
         │                           │
         ▼                           ▼

LAYER 5: ML & ANALYTICS (Depends on IAM, S3, ECR)
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│   ┌─────────────────────────┐   ┌────────────────────────────────┐                          │
│   │ MODULE: sagemaker       │   │ MODULE: sagemaker-studio       │                          │
│   │                         │   │                                │                          │
│   │ Creates:                │   │ Creates:                       │                          │
│   │ • SageMaker Model       │   │ • SageMaker Studio Domain      │                          │
│   │ • Endpoint Config       │   │ • Default User Settings        │                          │
│   │ • Endpoint              │   │ • Lifecycle Config             │                          │
│   │                         │   │   (MLflow integration)         │                          │
│   │ Name: fraud-score-dev   │   │                                │                          │
│   │ Instance: ml.m6g.large  │   │ Auth: IAM                      │                          │
│   │ Count: 1                │   │ VPC: PublicInternetOnly        │                          │
│   │                         │   │ Instance: ml.t3.medium         │                          │
│   │ Model Container:        │   │                                │                          │
│   │ • ECR image or          │   │ S3 Access:                     │                          │
│   │ • Built-in XGBoost      │   │ • raw, processed, models       │                          │
│   │ • Model data from S3    │   │ • mlflow artifacts             │                          │
│   │                         │   │                                │                          │
│   │ CloudWatch Alarms:      │   │ MLflow Integration:            │                          │
│   │ • 4xx > 10              │   │ • Auto-config notebooks        │                          │
│   │ • 5xx > 5               │   │ • MLFLOW_TRACKING_URI set      │                          │
│   │ • Latency p99 > 200ms   │   │                                │                          │
│   │                         │   │ CloudWatch Logs:               │                          │
│   │ Inputs:                 │   │ • 7 days retention             │                          │
│   │ • sagemaker_exec_role   │   │                                │                          │
│   │ • model_bucket_arn      │   │ Inputs:                        │                          │
│   │ • ecr_model_repo_url    │   │ • studio_exec_role             │                          │
│   │                         │   │ • s3_bucket_arns               │                          │
│   │ Outputs:                │   │ • mlflow_tracking_server       │                          │
│   │ • endpoint_name         │   │ • public_subnets               │                          │
│   │ • endpoint_arn          │   │                                │                          │
│   └─────────────────────────┘   │ Outputs:                       │                          │
│                                 │ • domain_id                    │                          │
│                                 │ • domain_url                   │                          │
│                                 └────────────────────────────────┘                          │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ DEPENDENCY SUMMARY                                                                              │
│                                                                                                 │
│ Total Modules: 12                                                                               │
│ Total Resources: 30+ AWS resources                                                              │
│                                                                                                 │
│ Critical Path:                                                                                  │
│   VPC → IAM → ALB → API Gateway                                                                 │
│   VPC → IAM → EKS → Kubernetes workloads                                                        │
│   S3 + IAM → SageMaker Endpoint → Inference                                                     │
│   S3 + IAM → MLflow → SageMaker Studio                                                          │
│                                                                                                 │
│ Independent Modules (parallel deployment):                                                      │
│   • S3, DynamoDB, SQS, ECR can be deployed in parallel after VPC                               │
│   • ALB and EKS can be deployed in parallel after VPC + IAM                                     │
│                                                                                                 │
│ Terraform Apply Order:                                                                          │
│   1. terraform apply -target=module.vpc                                                         │
│   2. terraform apply -target=module.s3 -target=module.dynamodb -target=module.sqs \            │
│                      -target=module.ecr                                                         │
│   3. terraform apply -target=module.iam                                                         │
│   4. terraform apply -target=module.alb -target=module.eks                                      │
│   5. terraform apply -target=module.api_gateway                                                 │
│   6. terraform apply -target=module.sagemaker -target=module.mlflow \                          │
│                      -target=module.sagemaker_studio                                            │
│   7. terraform apply (apply remaining resources)                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Matriz de Dependências

| Módulo | Depende de | Usado por |
|--------|-----------|-----------|
| vpc | - | alb, eks, s3 (endpoints), dynamodb (endpoints) |
| s3 | vpc (opcional) | iam, sagemaker, mlflow, studio |
| dynamodb | vpc (opcional) | iam |
| sqs | vpc (opcional) | iam, api-gateway |
| ecr | - | iam, sagemaker |
| mlflow | s3 | studio |
| iam | s3, dynamodb, sqs, ecr | alb, eks, sagemaker, mlflow, studio, api-gateway |
| alb | vpc, iam (opcional) | api-gateway |
| eks | vpc, iam (opcional) | - |
| api-gateway | alb, sqs, iam | - |
| sagemaker | s3, ecr, iam | - |
| sagemaker-studio | s3, mlflow, iam | - |

---

## Ordem Recomendada de Deployment

### Fase 1: Foundation (5-10 minutos)
```bash
terraform apply -target=module.vpc
```

**Cria:**
- VPC
- Subnets (4x)
- Internet Gateway
- Route Tables
- Security Groups
- VPC Endpoints (7x)

### Fase 2: Data Layer (5-10 minutos)
```bash
terraform apply \
  -target=module.s3 \
  -target=module.dynamodb \
  -target=module.sqs \
  -target=module.ecr \
  -target=module.mlflow
```

**Cria:**
- S3 buckets (4x)
- DynamoDB table
- SQS queues (2x)
- ECR repositories (3x)
- MLflow server

### Fase 3: Security (2-5 minutos)
```bash
terraform apply -target=module.iam
```

**Cria:**
- IAM roles (8x)
- IAM policies
- OIDC provider (GitHub Actions)

### Fase 4: Compute (10-15 minutos)
```bash
terraform apply \
  -target=module.alb \
  -target=module.eks
```

**Cria:**
- ALB + Target Group
- EKS cluster
- EKS node group
- Cluster addons

### Fase 5: API Layer (2-5 minutos)
```bash
terraform apply -target=module.api_gateway
```

**Cria:**
- REST API
- Resources (/v1/score, /health, /v1/result)
- Integrations
- Deployment + Stage

### Fase 6: ML Platform (5-10 minutos)
```bash
terraform apply \
  -target=module.sagemaker \
  -target=module.sagemaker_studio
```

**Cria:**
- SageMaker endpoint
- SageMaker Studio domain
- Lifecycle configs

### Fase 7: Finalize (1-2 minutos)
```bash
terraform apply
```

**Aplica quaisquer recursos remanescentes**

**Tempo total estimado:** 30-60 minutos

---

## Outputs Principais por Módulo

### VPC
```
vpc_id              = "vpc-xxxxx"
public_subnet_ids   = ["subnet-pub1", "subnet-pub2"]
private_subnet_ids  = ["subnet-priv1", "subnet-priv2"]
sg_alb_id           = "sg-xxxxx"
```

### EKS
```
cluster_name        = "elo-fraud-cluster-dev"
cluster_endpoint    = "https://xxxxx.eks.us-east-1.amazonaws.com"
oidc_provider_arn   = "arn:aws:iam::888577064416:oidc-provider/..."
```

### S3
```
raw_bucket_name       = "elo-fraud-data-raw-dev-888577064416"
processed_bucket_name = "elo-fraud-data-processed-dev-888577064416"
models_bucket_name    = "elo-fraud-models-dev-888577064416"
logs_bucket_name      = "elo-fraud-logs-dev-888577064416"
```

### SQS
```
queue_url  = "https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dev.fifo"
dlq_url    = "https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-transactions-dlq-dev.fifo"
```

### API Gateway
```
api_endpoint = "https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"
api_id       = "xxxxx"
```

### SageMaker
```
endpoint_name = "elo-fraud-fraud-score-dev"
endpoint_arn  = "arn:aws:sagemaker:us-east-1:888577064416:endpoint/elo-fraud-fraud-score-dev"
```

---

## Comandos Úteis

### Visualizar grafo de dependências
```bash
terraform graph | dot -Tpng > graph.png
```

### Listar todos os recursos
```bash
terraform state list
```

### Ver dependências de um módulo específico
```bash
terraform state show module.eks.aws_eks_cluster.main
```

### Plan apenas um módulo
```bash
terraform plan -target=module.vpc
```

### Destroy apenas um módulo
```bash
terraform destroy -target=module.sagemaker
```

**⚠️ CUIDADO:** Destroy pode quebrar dependências. Sempre verifique impacto antes.
