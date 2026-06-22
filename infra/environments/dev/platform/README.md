# Platform Stack - DEV

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Provisionados](#recursos-provisionados)
- [Pre-requisitos](#pre-requisitos)
- [Guia de Implantacao](#guia-de-implantacao)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Integracao com Outras Stacks](#integracao-com-outras-stacks)
- [Custos Estimados](#custos-estimados)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

A **Platform Stack** e a stack principal da aplicacao de deteccao de fraude. Provisiona todos os recursos necessarios para os fluxos de scoring em tempo real (sincrono) e processamento de feedback (assincrono).

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Compute** | EKS Cluster para execucao dos servicos de inferencia e processamento |
| **Networking** | ALB interno + NLB para integracao com API Gateway via VPC Link |
| **API** | API Gateway REST com endpoints `/v1/authorize-purchase` e `/health` |
| **Storage** | DynamoDB (feature store), SQS FIFO (fila de feedback), ECR (imagens Docker) |
| **Streaming** | Kinesis Firehose para entrega em batch de dados para S3 |
| **Analytics** | Athena + Glue para consultas SQL sobre dados historicos |
| **Observabilidade** | CloudWatch Dashboards para monitoramento de infraestrutura e API |

### Por que uma Stack Separada?

| Beneficio | Descricao |
|-----------|-----------|
| **Isolamento** | Mudancas na aplicacao nao afetam VPC/S3 (Foundation) ou MLflow (MLOps) |
| **Agilidade** | Deploy mais rapido - apenas recursos que mudam frequentemente |
| **Rollback** | Rollback independente em caso de problemas na aplicacao |
| **Seguranca** | Permissoes diferenciadas (dev vs infra admin) |

---

## Arquitetura

```
                              AWS Region: us-east-1
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              FLUXO SINCRONO (Scoring)                           │
│                                                                                 │
│   Cliente                                                                       │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│   │  API Gateway    │────▶│  VPC Link       │────▶│  NLB (interno)  │          │
│   │  (REGIONAL)     │     │                 │     │  TCP:80         │          │
│   │  /v1/authorize  │     │                 │     │                 │          │
│   └─────────────────┘     └─────────────────┘     └────────┬────────┘          │
│                                                             │                   │
│                                                             ▼                   │
│                                                  ┌─────────────────┐            │
│                                                  │  ALB (interno)  │            │
│                                                  │  HTTP:80        │            │
│                                                  │  /health check  │            │
│                                                  └────────┬────────┘            │
│                                                           │                     │
│                                                           ▼                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         EKS Cluster                                      │  │
│   │                                                                          │  │
│   │   ┌─────────────────┐              ┌─────────────────┐                  │  │
│   │   │  Inference Pod  │◀────────────▶│  Process Pod    │                  │  │
│   │   │  (scoring API)  │              │  (SQS worker)   │                  │  │
│   │   └────────┬────────┘              └────────┬────────┘                  │  │
│   │            │                                │                            │  │
│   └────────────┼────────────────────────────────┼────────────────────────────┘  │
│                │                                │                               │
│                ▼                                ▼                               │
│   ┌─────────────────┐              ┌─────────────────┐     ┌───────────────┐   │
│   │   DynamoDB      │              │   SQS FIFO      │────▶│  Firehose     │   │
│   │   (features)    │              │   (feedback)    │     │  (batch S3)   │   │
│   └─────────────────┘              └─────────────────┘     └───────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │ Consome via remote_state
                                        ▼

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Foundation Stack                                    │
│                                                                                  │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│   │     VPC       │  │    Subnets    │  │  S3 Buckets   │  │ VPC Endpoints │   │
│   │  10.0.0.0/16  │  │  pub + priv   │  │  raw/proc/    │  │  ECR, SQS,    │   │
│   │               │  │               │  │  models/logs  │  │  SageMaker    │   │
│   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados Detalhado

```
AUTHORIZE-PURCHASE (Sincrono - p95 < 500ms):
────────────────────────────────────────────────────────────────────────
   POST /v1/authorize-purchase
        │
        ▼
   API Gateway ──▶ VPC Link ──▶ NLB ──▶ ALB ──▶ Inference Pod
                                                       │
                                                       ├──▶ DynamoDB (GetItem - features)
                                                       │
                                                       └──▶ Response (score + recommendation)


FEEDBACK (Assincrono):
────────────────────────────────────────────────────────────────────────
   Elo Backend ──▶ SQS FIFO (boto3/SDK direto)
                         │
                         ▼
                   Process Pod (KEDA scaled)
                         │
                         ├──▶ DynamoDB (UpdateItem - fraud_label)
                         │
                         ├──▶ Firehose Transactions ──▶ S3 landing_zone/
                         │
                         └──▶ Firehose Inference ──▶ S3 inference_logs/


ETL (Batch - Semanal):
────────────────────────────────────────────────────────────────────────
   S3 landing_zone/
        │
        ▼
   Glue Job 1: job_training_test_1
   (Delta Lake MERGE)
        │
        ▼
   S3 transformed_zone/
        │
        ▼
   Glue Job 2: job_backfill_enrich
   (Feature Engineering)
        │
        ▼
   Athena Queries (SQL Analytics)
```

---

## Recursos Provisionados

### Compute

#### EKS Cluster

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-cluster-dev |
| **Versao Kubernetes** | 1.32 |
| **Endpoint Access** | Public + Private |
| **Subnets** | Privadas (10.0.11.0/24, 10.0.12.0/24) |
| **OIDC Provider** | Habilitado (para IRSA) |

#### EKS Node Group

| Atributo | Valor |
|----------|-------|
| **Instance Type** | t3.medium (2 vCPU, 4GB RAM) |
| **Min Nodes** | 1 |
| **Max Nodes** | 3 |
| **Desired Nodes** | 1 |
| **AMI Type** | AL2023_x86_64_STANDARD |

#### ALB (Application Load Balancer)

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-alb-dev |
| **Tipo** | Interno (nao exposto a internet) |
| **Subnets** | Privadas |
| **Listener** | HTTP:80 |
| **Target Group** | inference-tg-dev (type: ip) |
| **Health Check** | /health (HTTP, 30s interval) |
| **Idle Timeout** | 60s |

#### NLB (Network Load Balancer)

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-nlb-dev |
| **Tipo** | Interno (VPC Link) |
| **Subnets** | Privadas |
| **Listener** | TCP:80 |
| **Target** | ALB (type: alb) |
| **Cross-Zone** | Habilitado |

### API

#### API Gateway

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-api-dev |
| **Tipo** | REST (REGIONAL) |
| **VPC Link** | Habilitado (para NLB) |
| **Stage** | v1 |
| **Access Logs** | CloudWatch (30 dias) |
| **Throttle Burst** | 5000 req/s |
| **Throttle Rate** | 10000 req/s |

#### Endpoints

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/v1/authorize-purchase` | POST | Autorizacao de compra em tempo real (requer API Key) |
| `/health` | GET | Health check (sem API Key) |

### Storage

#### DynamoDB

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-customer-recent-tx-dev |
| **Billing Mode** | PAY_PER_REQUEST (on-demand) |
| **Partition Key** | cardHolderDocument (String) |
| **Sort Key** | transaction_id (Number) |
| **Encryption** | AWS managed |

#### SQS FIFO

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-resultset-dev.fifo |
| **Tipo** | FIFO (ordenado) |
| **Deduplicacao** | Content-based |
| **Visibility Timeout** | 300s (5 min) |
| **Message Retention** | 14 dias |
| **Receive Wait Time** | 20s (long polling) |
| **Encryption** | SQS managed (SSE-SQS) |

##### Dead Letter Queue (DLQ)

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-resultset-dlq-dev.fifo |
| **Max Receive Count** | 3 tentativas |

##### CloudWatch Alarms

| Alarm | Threshold |
|-------|-----------|
| Queue Depth | > 1000 mensagens |
| Message Age | > 600 segundos (10 min) |

#### ECR Repositories

| Repositorio | Nome | Finalidade |
|-------------|------|------------|
| **Inference** | elo-fraud-inference-dev | Servico de scoring |
| **Process** | elo-fraud-process-dev | Worker de processamento |
| **Model** | elo-fraud-model-dev | Imagem do modelo ML |

##### Configuracoes ECR

| Atributo | Valor |
|----------|-------|
| **Image Scanning** | Habilitado |
| **Tag Mutability** | MUTABLE (dev) |
| **Encryption** | AES256 |
| **Lifecycle** | 30 imagens, untagged 7 dias |

### Streaming

#### Kinesis Firehose - Transactions

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-transactions-firehose-dev |
| **Destino** | S3 (landing_zone/) |
| **Buffer Size** | 1 MB |
| **Buffer Interval** | 60 segundos |
| **Particionamento** | Hive-style (year=/month=/day=/hour=) |

#### Kinesis Firehose - Inference

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-inference-firehose-dev |
| **Destino** | S3 (inference_logs/) |
| **Buffer Size** | 1 MB |
| **Buffer Interval** | 60 segundos |

### Analytics

#### Athena

| Atributo | Valor |
|----------|-------|
| **Workgroup** | elo-fraud-athena-workgroup-dev |
| **Database** | elo_fraud_dev_db |
| **Query Limit** | 10 GB por query |

##### Tabelas Glue

| Tabela | Formato | Localizacao | Descricao |
|--------|---------|-------------|-----------|
| **transaction_results** | Delta Lake | transformed_zone/ | Dados processados |
| **inference_logs** | JSON | landing_zone/ | Logs brutos (Partition Projection) |

#### Glue ETL

| Job | Descricao | Schedule |
|-----|-----------|----------|
| **job_training_test_1** | Landing Zone → Transformed Zone (Delta MERGE) | Domingo 08:00 UTC |
| **job_backfill_enrich** | Feature Engineering | Apos job 1 (condicional) |

##### Configuracao dos Jobs

| Atributo | Valor |
|----------|-------|
| **Glue Version** | 5.0 |
| **Worker Type** | G.1X |
| **Number of Workers** | 10 |
| **Timeout** | 480 minutos (8h) |
| **Delta Lake** | Habilitado |

### Observabilidade

#### CloudWatch Dashboards

| Dashboard | Metricas |
|-----------|----------|
| **elo-fraud-infrastructure-dev** | SQS (depth, age, DLQ), DynamoDB (R/W, latency, throttle), Firehose |
| **elo-fraud-api-performance-dev** | API Gateway (count, latency p50/p95/p99, errors), ALB, NLB |

### Outros

#### Bedrock Agent IAM Role

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-bedrock-agent-dev |
| **Permissoes** | Athena, S3, Bedrock, Lambda |

---

## Pre-requisitos

### Dependencias

| Requisito | Descricao |
|-----------|-----------|
| **Bootstrap** | Stack de bootstrap aplicada |
| **Foundation** | Stack foundation aplicada (VPC, S3) |
| **MLOps** | Stack mlops aplicada (MLflow - para integracao) |
| **Terraform** | >= 1.10.0 |
| **AWS Provider** | ~> 5.0 |

### Permissoes AWS Necessarias

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:*",
        "elasticloadbalancing:*",
        "apigateway:*",
        "dynamodb:*",
        "sqs:*",
        "ecr:*",
        "firehose:*",
        "athena:*",
        "glue:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "logs:*",
        "cloudwatch:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

> **Nota:** Em producao, refine as permissoes para least privilege.

---

## Guia de Implantacao

### Primeira Execucao

```bash
# 1. Certifique-se que Foundation e MLOps foram aplicadas
cd infra/environments/dev/foundation
terraform output vpc_id  # Deve retornar um VPC ID

cd ../mlops
terraform output mlflow_tracking_uri  # Deve retornar um ARN

# 2. Navegue ate o diretorio Platform
cd ../platform

# 3. Inicialize o Terraform
terraform init

# 4. Visualize as mudancas
terraform plan

# 5. Aplique a infraestrutura
terraform apply

# 6. Verifique os outputs
terraform output
```

### Verificacao Pos-Implantacao

```bash
# Verificar EKS Cluster
aws eks describe-cluster \
  --name elo-fraud-cluster-dev \
  --region us-east-1 \
  --query 'cluster.status'

# Configurar kubectl
aws eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --region us-east-1

# Verificar nodes
kubectl get nodes

# Verificar API Gateway
terraform output api_gateway_invoke_url

# Testar health endpoint
curl $(terraform output -raw api_gateway_health_endpoint)

# Verificar DynamoDB
aws dynamodb describe-table \
  --table-name elo-fraud-customer-recent-tx-dev \
  --region us-east-1 \
  --query 'Table.TableStatus'

# Verificar SQS
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw sqs_queue_url) \
  --attribute-names All

# Verificar ECR
aws ecr describe-repositories \
  --repository-names elo-fraud-inference-dev \
  --region us-east-1

# Verificar Firehose
aws firehose describe-delivery-stream \
  --delivery-stream-name elo-fraud-transactions-firehose-dev \
  --region us-east-1 \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'

# Verificar Dashboards
terraform output cloudwatch_dashboard_url
terraform output cloudwatch_dashboard_api_performance_url
```

---

## Estrutura de Arquivos

```
infra/environments/dev/platform/
├── main.tf              # (vazio - recursos em arquivos especificos)
├── data.tf              # Remote states (Foundation, MLOps)
├── compute.tf           # EKS Cluster e Node Group
├── alb.tf               # Application Load Balancer
├── nlb.tf               # Network Load Balancer (VPC Link)
├── api.tf               # API Gateway REST + VPC Link
├── storage.tf           # DynamoDB, SQS, ECR
├── streaming.tf         # Kinesis Firehose (2 streams)
├── analytics.tf         # Athena Workgroup e Database
├── glue.tf              # Glue Jobs, Triggers, S3 Assets
├── monitoring.tf        # CloudWatch Dashboards
├── security.tf          # IAM Roles (Bedrock Agent)
├── lambda.tf            # Lambda ETL Delta Filter
├── variables.tf         # Definicao de variaveis
├── outputs.tf           # Outputs para outras stacks
├── backend.tf           # Backend S3
├── providers.tf         # Provider AWS
└── README.md            # Esta documentacao
```

### Descricao dos Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `data.tf` | Le outputs de Foundation e MLOps via remote state |
| `compute.tf` | Modulo EKS para cluster Kubernetes |
| `alb.tf` | Modulo ALB interno para roteamento de trafego |
| `nlb.tf` | Modulo NLB para integracao com VPC Link |
| `api.tf` | Modulo API Gateway com VPC Link |
| `storage.tf` | Modulos DynamoDB, SQS FIFO e ECR |
| `streaming.tf` | Modulos Firehose para transactions e inference |
| `analytics.tf` | Modulo Athena com Glue Database |
| `glue.tf` | Jobs ETL, triggers e bucket de assets |
| `monitoring.tf` | Dashboards de infraestrutura e API performance |
| `security.tf` | Modulo IAM para Bedrock Agent |
| `lambda.tf` | Lambda para processamento delta de dados |
| `variables.tf` | Variaveis configuraveis da stack |
| `outputs.tf` | Exporta valores para platform-k8s e platform-lambdas |

---

## Variaveis

### Gerais

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `project_name` | string | `elo-fraud` | Nome do projeto |
| `environment` | string | `dev` | Ambiente |
| `aws_region` | string | `us-east-1` | Regiao AWS |
| `aws_account_id` | string | `888577064416` | ID da conta AWS |

### EKS

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `cluster_version` | string | `1.32` | Versao do Kubernetes |
| `node_instance_types` | list(string) | `["t3.medium"]` | Tipos de instancia |
| `node_min_size` | number | `1` | Minimo de nodes |
| `node_max_size` | number | `3` | Maximo de nodes |
| `node_desired_size` | number | `1` | Nodes desejados |

### VPC (Referencia)

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `vpc_cidr` | string | `10.0.0.0/16` | CIDR da VPC (referencia) |
| `availability_zones` | list(string) | `["us-east-1a", "us-east-1b"]` | AZs |

### Tags

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `common_tags` | map(string) | Ver abaixo | Tags comuns |

```hcl
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Platform"
  Region      = "us-east-1"
}
```

---

## Outputs

### EKS

| Output | Descricao |
|--------|-----------|
| `eks_cluster_id` | ID do cluster |
| `eks_cluster_name` | Nome do cluster |
| `eks_cluster_endpoint` | Endpoint do API server |
| `eks_cluster_version` | Versao do Kubernetes |
| `eks_oidc_provider_arn` | ARN do OIDC provider (IRSA) |
| `eks_oidc_provider_url` | URL do OIDC provider |
| `eks_node_group_id` | ID do node group |
| `eks_kubeconfig_command` | Comando para configurar kubectl |

### ALB / NLB

| Output | Descricao |
|--------|-----------|
| `alb_dns_name` | DNS do ALB interno |
| `alb_arn` | ARN do ALB |
| `alb_internal` | Indica se ALB e interno (true) |
| `target_group_arn` | ARN do Target Group (para K8s) |
| `nlb_dns_name` | DNS do NLB |
| `nlb_arn` | ARN do NLB |
| `nlb_zone_id` | Zone ID do NLB (para Route53) |

### API Gateway

| Output | Descricao |
|--------|-----------|
| `api_gateway_id` | ID da REST API |
| `api_gateway_invoke_url` | URL base de invocacao |
| `api_gateway_authorize_purchase_endpoint` | URL do POST /v1/authorize-purchase |
| `api_gateway_health_endpoint` | URL do GET /health |

### DynamoDB

| Output | Descricao |
|--------|-----------|
| `dynamodb_table_name` | Nome da tabela |
| `dynamodb_table_arn` | ARN da tabela |
| `dynamodb_summary` | Resumo da configuracao |

### SQS

| Output | Descricao |
|--------|-----------|
| `sqs_queue_url` | URL da fila principal |
| `sqs_queue_arn` | ARN da fila principal |
| `sqs_queue_name` | Nome da fila |
| `sqs_dlq_url` | URL da DLQ |
| `sqs_dlq_arn` | ARN da DLQ |

### ECR

| Output | Descricao |
|--------|-----------|
| `ecr_inference_repository_url` | URL do repo inference |
| `ecr_process_repository_url` | URL do repo process |
| `ecr_model_repository_url` | URL do repo model |
| `ecr_all_repository_arns` | Lista de ARNs |

### Firehose

| Output | Descricao |
|--------|-----------|
| `firehose_delivery_stream_name` | Nome do stream transactions |
| `firehose_delivery_stream_arn` | ARN do stream transactions |
| `firehose_inference_delivery_stream_name` | Nome do stream inference |
| `firehose_inference_delivery_stream_arn` | ARN do stream inference |

### Athena / Glue

| Output | Descricao |
|--------|-----------|
| `athena_database_name` | Nome do database Glue |
| `athena_table_name` | Nome da tabela transaction_results |
| `athena_workgroup_name` | Nome do workgroup |
| `athena_results_bucket` | Bucket de resultados |
| `glue_role_arn` | ARN da role Glue |

### CloudWatch

| Output | Descricao |
|--------|-----------|
| `cloudwatch_dashboard_infrastructure_name` | Nome do dashboard infra |
| `cloudwatch_dashboard_url` | URL do dashboard infra |
| `cloudwatch_dashboard_api_performance_name` | Nome do dashboard API |
| `cloudwatch_dashboard_api_performance_url` | URL do dashboard API |

### S3 Paths (Data Lake)

| Output | Descricao |
|--------|-----------|
| `s3_landing_zone_path` | Path da landing zone |
| `s3_transformed_zone_path` | Path da transformed zone |
| `s3_inference_logs_path` | Path dos inference logs |
| `s3_query_results_path` | Path dos resultados de query |
| `s3_delta_zone_path` | Path da delta zone (ETL Delta Filter) |

### Bedrock Agent

| Output | Descricao |
|--------|-----------|
| `bedrock_agent_role_arn` | ARN da IAM Role para Bedrock Agent |
| `bedrock_agent_role_name` | Nome da IAM Role para Bedrock Agent |

### Lambda ETL

| Output | Descricao |
|--------|-----------|
| `lambda_etl_delta_filter_name` | Nome da Lambda ETL Delta Filter |
| `lambda_etl_delta_filter_arn` | ARN da Lambda ETL Delta Filter |

---

## Integracao com Outras Stacks

### Dependencias (Consome)

```
Foundation ──────────▶ Platform
    │
    ├── vpc_id
    ├── vpc_cidr
    ├── public_subnet_ids
    ├── private_subnet_ids
    ├── security_group_alb_id
    ├── s3_raw_bucket_arn
    ├── s3_processed_bucket_arn
    ├── s3_processed_bucket_id
    ├── s3_models_bucket_arn
    └── s3_logs_bucket_arn

MLOps ───────────────▶ Platform
    │
    ├── mlflow_tracking_uri
    ├── mlflow_tracking_server_arn
    ├── mlflow_tracking_server_url
    └── mlflow_artifact_bucket_arn
```

### Dependentes (Fornece)

```
Platform ──────────────▶ Platform-K8s
    │
    ├── eks_cluster_name
    ├── eks_cluster_endpoint
    ├── eks_oidc_provider_arn
    ├── vpc_id
    ├── target_group_arn
    ├── sqs_queue_url
    ├── sqs_queue_name
    ├── dynamodb_table_name
    ├── firehose_delivery_stream_name
    └── s3_processed_bucket_id

Platform ──────────────▶ Platform-Lambdas
    │
    ├── ecr_register_best_model_url
    └── ecr_register_best_model_arn
```

### Como Consumir os Outputs

```hcl
# Em platform-k8s/data.tf
data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/platform/terraform.tfstate"
    region = "us-east-1"
  }
}

# Uso:
locals {
  eks_cluster_name = data.terraform_remote_state.platform.outputs.eks_cluster_name
  target_group_arn = data.terraform_remote_state.platform.outputs.target_group_arn
  sqs_queue_url    = data.terraform_remote_state.platform.outputs.sqs_queue_url
}
```

### Ordem de Implantacao

```
1. bootstrap
       │
       ▼
2. foundation
       │
       ├──────────────────┐
       ▼                  ▼
3. mlops            platform ◀── ESTA STACK
                          │
                          ▼
                    platform-k8s
                          │
                          ▼
                    platform-lambdas
```

---

## Custos Estimados

### Resumo Mensal (DEV)

| Recurso | Quantidade | Custo Unitario | Custo Total |
|---------|------------|----------------|-------------|
| **EKS Control Plane** | 1 | $73.00/mes | $73.00 |
| **EKS Node (t3.medium)** | 1 | ~$30.00/mes | ~$30.00 |
| **ALB** | 1 | ~$16.00/mes | ~$16.00 |
| **NLB** | 1 | ~$18.00/mes | ~$18.00 |
| **API Gateway** | Pay-per-request | ~$0-5/mes | ~$2.00 |
| **DynamoDB** | On-demand | ~$0-5/mes | ~$2.00 |
| **SQS** | Pay-per-request | ~$0-1/mes | ~$0.50 |
| **ECR** | Storage | ~$1/mes | ~$1.00 |
| **Firehose** | 2 streams | ~$3/mes | ~$3.00 |
| **Athena** | Queries | ~$5/mes | ~$5.00 |
| **Glue Jobs** | Eventual | ~$0.44/hora | ~$5.00 |
| **CloudWatch** | Dashboards + Logs | ~$10/mes | ~$10.00 |
| | | **Total Estimado** | **~$165.50** |

### Otimizacoes Aplicadas

| Otimizacao | Economia |
|------------|----------|
| EKS 1 node (em vez de 3) | ~$60/mes |
| DynamoDB on-demand | Pay-per-use |
| ALB/NLB internos | Sem NAT para trafego |
| Firehose buffer minimo | Entrega rapida em dev |
| Glue jobs semanais | Reduz horas de execucao |

---

## Operacoes

### Configurar kubectl

```bash
# Configurar acesso ao cluster
aws eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --region us-east-1

# Verificar conexao
kubectl cluster-info
kubectl get nodes
```

### Push de Imagem Docker para ECR

```bash
# Login no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

# Build e push
docker build -t elo-fraud-inference-dev:latest ./services/inference
docker tag elo-fraud-inference-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest
docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest
```

### Testar API Gateway

```bash
# Health check (sem API Key)
curl $(terraform output -raw api_gateway_health_endpoint)

# Obter API Key
API_KEY=$(terraform output -json api_gateway_api_keys | jq -r '.["elo-backend"]')

# Authorize Purchase request (com API Key)
curl -X POST $(terraform output -raw api_gateway_authorize_purchase_endpoint) \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"cardHolderDocument": "12345678901", "transaction_id": 1}'
```

### Verificar Metricas SQS

```bash
# Profundidade da fila
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw sqs_queue_url) \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1

# Mensagens na DLQ
aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw sqs_dlq_url) \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1
```

### Executar Query no Athena

```bash
# Via AWS CLI
aws athena start-query-execution \
  --query-string "SELECT * FROM transaction_results LIMIT 10" \
  --query-execution-context Database=elo_fraud_dev_db \
  --work-group elo-fraud-athena-workgroup-dev \
  --region us-east-1
```

### Executar Glue Job Manualmente

```bash
# Iniciar job
aws glue start-job-run \
  --job-name job_training_test_1 \
  --region us-east-1

# Verificar status
aws glue get-job-run \
  --job-name job_training_test_1 \
  --run-id <RUN_ID> \
  --region us-east-1
```

### Destruir Infraestrutura

```bash
# ATENCAO: Destruir na ordem reversa
# 1. platform-lambdas
# 2. platform-k8s
# 3. platform (esta stack)

# Esvaziar buckets S3 (Glue assets)
aws s3 rm s3://aws-glue-assets-888577064416-us-east-1 --recursive

# Destruir
terraform destroy
```

---

## Troubleshooting

### Erro: EKS Cluster nao inicia

**Sintoma:**
```
Error: error creating EKS Cluster: InvalidParameterException
```

**Causa:** Subnets invalidas ou sem tags corretas para EKS.

**Solucao:**
```bash
# Verificar subnets tem tags necessarias
aws ec2 describe-subnets \
  --subnet-ids subnet-xxx \
  --query 'Subnets[*].Tags'

# Tags necessarias para EKS:
# kubernetes.io/cluster/<cluster-name> = shared
# kubernetes.io/role/internal-elb = 1 (private)
```

### Erro: ALB Health Check falha

**Sintoma:**
```
Target Group: unhealthy targets
```

**Causa:** Pods nao respondem em /health ou Security Group bloqueando.

**Solucao:**
```bash
# Verificar pods estao rodando
kubectl get pods -n fraud-detection

# Verificar logs do pod
kubectl logs -f deployment/inference -n fraud-detection

# Verificar Security Group permite porta 8000
aws ec2 describe-security-groups --group-ids sg-xxx
```

### Erro: API Gateway 5XX

**Sintoma:**
```
{"message":"Internal Server Error"}
```

**Causa:** VPC Link nao conecta ao NLB ou NLB nao conecta ao ALB.

**Solucao:**
```bash
# Verificar VPC Link status
aws apigateway get-vpc-links --region us-east-1

# Verificar NLB targets
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn)

# Verificar ALB targets
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn)
```

### Erro: SQS mensagens na DLQ

**Sintoma:**
Mensagens aparecendo na DLQ.

**Causa:** Process worker falhando 3x consecutivas.

**Solucao:**
```bash
# Ver mensagens na DLQ
aws sqs receive-message \
  --queue-url $(terraform output -raw sqs_dlq_url) \
  --max-number-of-messages 1

# Verificar logs do process worker
kubectl logs -f deployment/process -n fraud-detection

# Reprocessar mensagens (mover DLQ -> fila principal)
# Use Lambda ou script customizado
```

### Erro: Firehose delivery failed

**Sintoma:**
```
DeliveryToS3.DataFreshness increasing
```

**Causa:** Bucket S3 nao acessivel ou IAM Role sem permissao.

**Solucao:**
```bash
# Verificar logs do Firehose
aws logs get-log-events \
  --log-group-name /aws/kinesisfirehose/elo-fraud-transactions-firehose-dev \
  --log-stream-name $(aws logs describe-log-streams \
    --log-group-name /aws/kinesisfirehose/elo-fraud-transactions-firehose-dev \
    --query 'logStreams[0].logStreamName' --output text)

# Verificar IAM Role do Firehose
aws iam get-role --role-name $(terraform output -raw firehose_role_arn | cut -d'/' -f2)
```

### Erro: Glue Job falha

**Sintoma:**
```
Job status: FAILED
```

**Causa:** Script Python com erro ou paths S3 incorretos.

**Solucao:**
```bash
# Ver logs do job
aws logs get-log-events \
  --log-group-name /aws-glue/jobs/output \
  --log-stream-name job_training_test_1/<RUN_ID>

# Verificar script no S3
aws s3 cp s3://aws-glue-assets-888577064416-us-east-1/scripts/job_training_test_1.py ./

# Verificar paths de input/output existem
aws s3 ls s3://elo-fraud-data-processed-dev-888577064416/landing_zone/
```

### Erro: ECR pull failed nos pods

**Sintoma:**
```
ErrImagePull: failed to pull image
```

**Causa:** VPC Endpoint de ECR nao configurado ou node sem permissao.

**Solucao:**
```bash
# Verificar VPC Endpoints de ECR
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=*ecr*" \
  --query 'VpcEndpoints[*].[VpcEndpointId,State,ServiceName]'

# Verificar node IAM role tem AmazonEC2ContainerRegistryReadOnly
aws iam list-attached-role-policies \
  --role-name elo-fraud-node-role-dev
```

