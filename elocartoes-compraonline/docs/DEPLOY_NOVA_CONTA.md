# Deploy Completo — Nova Conta AWS

Guia passo a passo para subir toda a infraestrutura do Elo Fraud Detection em uma nova conta AWS.

**Tempo estimado**: ~90 minutos
**Ordem obrigatória**: Bootstrap → Foundation → MLOps → Platform → Docker Images → Platform-K8s → K8s Manifests → Platform-Lambdas → Validação

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Variáveis da Nova Conta](#2-variáveis-da-nova-conta)
3. [Fase 0 — Bootstrap (State Bucket)](#3-fase-0--bootstrap-state-bucket)
4. [Fase 1 — Foundation (VPC, S3)](#4-fase-1--foundation-vpc-s3)
5. [Fase 2 — MLOps (MLflow, SageMaker Studio)](#5-fase-2--mlops-mlflow-sagemaker-studio)
6. [Fase 3 — Platform (EKS, ALB, NLB, API GW, DynamoDB, SQS, Firehose, Glue, Athena, ECR)](#6-fase-3--platform)
7. [Fase 4 — Docker Images (Build & Push ECR)](#7-fase-4--docker-images-build--push-ecr)
8. [Fase 5 — Platform-K8s (Helm, HPA, KEDA, ConfigMaps)](#8-fase-5--platform-k8s)
9. [Fase 6 — K8s Manifests (kubectl)](#9-fase-6--k8s-manifests-kubectl)
10. [Fase 7 — Platform-Lambdas (3 Lambda Functions)](#10-fase-7--platform-lambdas)
11. [Fase 8 — Validação E2E](#11-fase-8--validação-e2e)
12. [Referência — Arquitetura de Rede](#12-referência--arquitetura-de-rede)
13. [Referência — Recursos Criados](#13-referência--recursos-criados)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Pré-requisitos

### Ferramentas

```bash
# Verificar versões
terraform --version   # >= 1.14.4
aws --version         # >= 2.15.0
kubectl version       # >= 1.30.0
helm version          # >= 3.14.0
docker --version      # >= 24.0.0
```

### Instalar Terraform (se necessário)

```bash
TF_VERSION="1.14.4"
curl -sLO "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip"
unzip -o "terraform_${TF_VERSION}_linux_amd64.zip" -d /usr/local/bin/
terraform --version
```

### Configurar AWS CLI

```bash
# Configurar profile para a nova conta
aws configure sso --profile <PROFILE_NAME>
# SSO start URL: <URL_DO_SSO>
# SSO Region: <REGIÃO_DO_SSO>
# Account ID: <NOVO_ACCOUNT_ID>
# Role: AdministratorAccess (ou equivalente)
# Default region: <REGIÃO_DO_DEPLOY>

# Login
aws sso login --profile <PROFILE_NAME>

# Verificar
aws sts get-caller-identity --profile <PROFILE_NAME>
```

### Permissões IAM necessárias

O usuário/role precisa de permissões para:
- VPC, Subnets, NAT Gateway, Internet Gateway, VPC Endpoints
- S3, DynamoDB, SQS, Kinesis Firehose
- EKS, ECR, EC2 (Auto Scaling Groups, Security Groups)
- ALB, NLB, API Gateway
- Lambda, Glue, Athena, SageMaker, MLflow
- IAM (roles, policies — sujeito a SCPs)
- CloudWatch (logs, dashboards, alarms)

> **Nota sobre SCPs**: Se a conta tiver SCPs restritivas, verificar:
> - `iam:CreateOpenIDConnectProvider` bloqueado → IRSA não funciona, pods usam Node IAM Role
> - `iam:TagRole` bloqueado → desabilitar `default_tags` no provider Terraform
> - `iam:CreatePolicy` limitado → usar somente AWS Managed Policies

---

## 2. Variáveis da Nova Conta

Antes de começar, definir estas variáveis (usar em todos os comandos):

```bash
# === ALTERAR ESTES VALORES ===
export ACCOUNT_ID="<NOVO_ACCOUNT_ID>"         # ex: 123456789012
export AWS_REGION="<REGIÃO>"                   # ex: us-east-1
export ENVIRONMENT="<AMBIENTE>"                # ex: dev, staging, prod
export PROFILE="<PROFILE_NAME>"                # ex: elo
export PROJECT_NAME="elo-fraud"

# === DERIVADOS (não alterar) ===
export TF_STATE_BUCKET="${PROJECT_NAME}-terraform-state-${ACCOUNT_ID}-${AWS_REGION}"
export TF_STATE_REGION="${AWS_REGION}"
```

### Valores de rede por ambiente (sugestão)

| Ambiente | Região | VPC CIDR | Public Subnets | Private Subnets |
|---|---|---|---|---|
| dev | us-east-1 | 10.0.0.0/16 | 10.0.1.0/24, 10.0.2.0/24 | 10.0.11.0/24, 10.0.12.0/24 |
| staging | sa-east-1 | 10.1.0.0/16 | 10.1.1.0/24, 10.1.2.0/24 | 10.1.11.0/24, 10.1.12.0/24 |
| test | us-east-2 | 10.2.0.0/16 | 10.2.1.0/24, 10.2.2.0/24 | 10.2.11.0/24, 10.2.12.0/24 |

---

## 3. Fase 0 — Bootstrap (State Bucket)

Cria o bucket S3 centralizado para armazenar o state de todas as stacks.

```bash
cd infra/bootstrap

# Inicializar (state local, apenas para o bootstrap)
terraform init

# Aplicar
terraform apply \
  -var="state_bucket_name=${TF_STATE_BUCKET}" \
  -var="aws_region=${AWS_REGION}"

# Verificar
aws s3 ls s3://${TF_STATE_BUCKET} --profile ${PROFILE} --region ${AWS_REGION}
```

**Outputs gerados:**
- `terraform_state_bucket_name` — usado por todas as stacks
- `terraform_state_bucket_arn`

---

## 4. Fase 1 — Foundation (VPC, S3)

### 4.1. Preparar o diretório

```bash
# Se criando novo ambiente, copiar do dev como base
mkdir -p infra/environments/${ENVIRONMENT}/foundation
cp infra/environments/dev/foundation/*.tf infra/environments/${ENVIRONMENT}/foundation/
```

### 4.2. Configurar backend.tf

Editar `infra/environments/${ENVIRONMENT}/foundation/backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket       = "<TF_STATE_BUCKET>"            # elo-fraud-terraform-state-{ACCOUNT}-{REGION}
    key          = "<ENVIRONMENT>/foundation/terraform.tfstate"
    region       = "<TF_STATE_REGION>"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 4.3. Configurar terraform.tfvars

Criar `infra/environments/${ENVIRONMENT}/foundation/terraform.tfvars`:

```hcl
project_name   = "elo-fraud"
environment    = "<ENVIRONMENT>"
aws_region     = "<AWS_REGION>"
aws_account_id = "<ACCOUNT_ID>"

# VPC
vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["<REGION>a", "<REGION>b"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# Rede
enable_nat_gateway         = true     # ~$32/mês (necessário para EKS pull images)
single_nat_gateway         = true     # 1 NAT para economia (dev/staging)
enable_vpc_endpoints       = true     # Gateway endpoints (S3, DynamoDB) — gratuitos
enable_interface_endpoints = true     # 9 Interface endpoints — ~$130/mês
```

### 4.4. Deploy

```bash
cd infra/environments/${ENVIRONMENT}/foundation

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Verificar outputs
terraform output
```

**Recursos criados:**
- VPC com 4 subnets (2 public, 2 private)
- Internet Gateway
- NAT Gateway (single)
- Route Tables
- VPC Gateway Endpoints (S3, DynamoDB)
- 9 VPC Interface Endpoints (ECR API/DKR, CloudWatch, SQS, STS, EC2, SageMaker, Firehose)
- 7 S3 buckets (raw, processed, models, logs, resources, reports-promotion, reports-statistics)

---

## 5. Fase 2 — MLOps (MLflow, SageMaker Studio)

### 5.1. Preparar o diretório

```bash
mkdir -p infra/environments/${ENVIRONMENT}/mlops
cp infra/environments/dev/mlops/*.tf infra/environments/${ENVIRONMENT}/mlops/
```

### 5.2. Configurar backend.tf

```hcl
terraform {
  backend "s3" {
    bucket       = "<TF_STATE_BUCKET>"
    key          = "<ENVIRONMENT>/mlops/terraform.tfstate"
    region       = "<TF_STATE_REGION>"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 5.3. Atualizar data.tf (referência à Foundation)

```hcl
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/foundation/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}
```

### 5.4. Configurar terraform.tfvars

```hcl
project_name       = "elo-fraud"
environment        = "<ENVIRONMENT>"
mlflow_environment = "<ENVIRONMENT>"
aws_region         = "<AWS_REGION>"

# MLflow
tracking_server_size            = "Small"
mlflow_version                  = "3.0"
weekly_maintenance_window_start = "Sun:03:00"
log_retention_days              = 7

# SageMaker Studio
default_notebook_instance_type = "ml.t3.medium"
idle_timeout_in_minutes        = 60
sagemaker_user_profile_name    = "elo-fraud-ml-user"
```

### 5.5. Deploy

```bash
cd infra/environments/${ENVIRONMENT}/mlops

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Guardar o ARN do MLflow (necessário na Fase 7)
terraform output -raw mlflow_tracking_server_arn
```

**Recursos criados:**
- MLflow Tracking Server (SageMaker Managed)
- S3 bucket para artefatos MLflow
- SageMaker Studio Domain
- IAM execution roles
- CloudWatch log groups

### 5.6. Extrair MLflow App ARN (IMPORTANTE)

Após o deploy, o SageMaker Studio cria automaticamente uma MLflow App. O ARN dela é diferente do Tracking Server:

```bash
# Listar apps do Studio
aws sagemaker list-domains --profile ${PROFILE} --region ${AWS_REGION} --output json

# O ARN da MLflow App tem o formato:
# arn:aws:sagemaker:{region}:{account}:mlflow-app/app-{ID}
#
# Este ARN será usado nas Lambdas (Fase 7).
# Anotar este valor:
export MLFLOW_APP_ARN="arn:aws:sagemaker:${AWS_REGION}:${ACCOUNT_ID}:mlflow-app/app-XXXXXXXXXX"
```

---

## 6. Fase 3 — Platform

Stack mais complexa. Cria EKS, ALB, NLB, API Gateway, DynamoDB, SQS, Firehose, Glue, Athena e ECR.

### 6.1. Preparar o diretório

```bash
mkdir -p infra/environments/${ENVIRONMENT}/platform
cp infra/environments/dev/platform/*.tf infra/environments/${ENVIRONMENT}/platform/
```

### 6.2. Configurar backend.tf

```hcl
terraform {
  backend "s3" {
    bucket       = "<TF_STATE_BUCKET>"
    key          = "<ENVIRONMENT>/platform/terraform.tfstate"
    region       = "<TF_STATE_REGION>"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 6.3. Atualizar data.tf (referências remotas)

```hcl
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/foundation/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}

data "terraform_remote_state" "mlops" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/mlops/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}
```

### 6.4. Configurar terraform.tfvars

```hcl
project_name   = "elo-fraud"
environment    = "<ENVIRONMENT>"
aws_region     = "<AWS_REGION>"
aws_account_id = "<ACCOUNT_ID>"

# EKS
cluster_version     = "1.32"
node_instance_types = ["t3.medium"]   # 2 vCPU, 4GB RAM
node_min_size       = 1
node_max_size       = 3
node_desired_size   = 1

# DynamoDB
dynamodb_hash_key  = "acctID"
dynamodb_range_key = "threeDSServerTransID"

# SQS FIFO
sqs_visibility_timeout_seconds = 300
sqs_message_retention_seconds  = 345600    # 4 dias
sqs_receive_wait_time_seconds  = 20
sqs_max_receive_count          = 3

# ALB (internal)
alb_target_group_port     = 8000
alb_deregistration_delay  = 30
alb_health_check_interval = 15
alb_health_check_timeout  = 5
alb_healthy_threshold     = 2
alb_unhealthy_threshold   = 3
alb_idle_timeout          = 60

# NLB (internal, VPC Link)
nlb_target_port           = 80
nlb_listener_port         = 80

# Firehose
firehose_buffer_size_mb          = 1
firehose_buffer_interval_seconds = 60

# API Gateway
api_gateway_stage_name                 = "v1"
api_gateway_stage_throttle_burst_limit = 5000
api_gateway_stage_throttle_rate_limit  = 2000
api_gateway_usage_plan_quota_limit     = 1000000
inference_service_port                 = 8000

# Glue ETL
glue_version           = "5.0"
glue_worker_type       = "G.1X"
glue_number_of_workers = 2
glue_job_timeout       = 30
glue_max_retries       = 0
glue_training_job_name = "job_training_test_1"
glue_enrich_job_name   = "job_backfill_enrich"
glue_training_schedule = "cron(0 8 ? * SUN *)"

# Data Lake prefixes
s3_prefix_landing_zone     = "landing_zone"
s3_prefix_transformed_zone = "transformed_zone"
s3_prefix_inference_logs   = "inference_logs"

# Athena
athena_bytes_scanned_limit = 1073741824   # 1 GB
athena_force_destroy       = true
```

### 6.5. Deploy

```bash
cd infra/environments/${ENVIRONMENT}/platform

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Guardar outputs para as próximas fases
terraform output
```

> **Nota**: O EKS cluster demora ~10-15 minutos para ficar ACTIVE.

**Recursos criados:**
- EKS Cluster + Managed Node Group
- ALB (internal) + Target Group (port 8000)
- NLB (internal) + VPC Link
- API Gateway REST API (regional)
- DynamoDB Table (on-demand)
- SQS FIFO Queue + DLQ
- Firehose Streams (2: transactions + inference logs)
- Glue ETL Jobs (2) + Trigger semanal
- Athena Database + Tables
- ECR Repositories (6: 3 services + 3 lambdas)
- CloudWatch Dashboards (2) + Alarms
- IAM Roles (Glue, Bedrock)
- Security Group Rules

### 6.6. Configurar kubectl

```bash
aws eks update-kubeconfig \
  --name ${PROJECT_NAME}-cluster-${ENVIRONMENT} \
  --region ${AWS_REGION} \
  --profile ${PROFILE}

# Verificar conexão
kubectl get nodes
kubectl cluster-info
```

---

## 7. Fase 4 — Docker Images (Build & Push ECR)

### 7.1. Login no ECR

```bash
aws ecr get-login-password --region ${AWS_REGION} --profile ${PROFILE} | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

### 7.2. Build & Push — Serviço Inference

```bash
cd services/inference
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-inference-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-inference-${ENVIRONMENT}:latest
```

### 7.3. Build & Push — Serviço Process

```bash
cd services/process
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-process-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-process-${ENVIRONMENT}:latest
```

### 7.4. Build & Push — Model Training (SageMaker)

```bash
cd models/mix_models
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-model-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-model-${ENVIRONMENT}:latest
```

> **Nota**: O Dockerfile do modelo precisa existir em `models/mix_models/Dockerfile`.
> Se não existir, verificar a branch `feat#53/sagemaker_job` ou criar a partir do código em `models/src/`.

### 7.5. Build & Push — Lambda register-best-model

```bash
cd lambdas/register-best-model
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/best-model-register-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/best-model-register-${ENVIRONMENT}:latest
```

### 7.6. Build & Push — Lambda etl-delta-filter

```bash
cd lambdas/etl-delta-filter
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/etl-delta-filter-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/etl-delta-filter-${ENVIRONMENT}:latest
```

### 7.7. Build & Push — Lambda training-launcher

```bash
cd lambdas/training-launcher
docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/training-launcher-${ENVIRONMENT}:latest .
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/training-launcher-${ENVIRONMENT}:latest
```

### 7.8. Verificar todas as imagens

```bash
for REPO in ${PROJECT_NAME}-inference-${ENVIRONMENT} ${PROJECT_NAME}-process-${ENVIRONMENT} ${PROJECT_NAME}-model-${ENVIRONMENT} best-model-register-${ENVIRONMENT} etl-delta-filter-${ENVIRONMENT} training-launcher-${ENVIRONMENT}; do
  echo "=== ${REPO} ==="
  aws ecr list-images --repository-name ${REPO} --region ${AWS_REGION} --profile ${PROFILE} --query 'imageIds[*].imageTag' --output text 2>/dev/null || echo "VAZIO"
done
```

---

## 8. Fase 5 — Platform-K8s

Instala addons Kubernetes (Helm), configura autoscaling, ConfigMaps e TargetGroupBinding.

### 8.1. Preparar o diretório

```bash
mkdir -p infra/environments/${ENVIRONMENT}/platform-k8s
cp infra/environments/dev/platform-k8s/*.tf infra/environments/${ENVIRONMENT}/platform-k8s/
```

### 8.2. Configurar backend.tf

```hcl
terraform {
  backend "s3" {
    bucket       = "<TF_STATE_BUCKET>"
    key          = "<ENVIRONMENT>/platform-k8s/terraform.tfstate"
    region       = "<TF_STATE_REGION>"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 8.3. Atualizar data.tf

```hcl
data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/platform/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}
```

### 8.4. Configurar terraform.tfvars

```hcl
project_name = "elo-fraud"
environment  = "<ENVIRONMENT>"
aws_region   = "<AWS_REGION>"
```

### 8.5. Deploy

```bash
cd infra/environments/${ENVIRONMENT}/platform-k8s

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

**Recursos criados (via Terraform):**
- Namespace `fraud-detection`
- Helm: metrics-server v3.13.0
- Helm: cluster-autoscaler v9.55.0
- Helm: aws-load-balancer-controller v3.0.0
- Helm: KEDA v2.18.3
- HPA (inference: 2-6 replicas, CPU 50%, Memory 75%)
- ScaledObject KEDA (process: 1-5 replicas, 30 msgs/pod)
- PodDisruptionBudgets (inference + process)
- ConfigMap `inference-config`
- ConfigMap `process-config`
- TargetGroupBinding (ALB → inference service port 8000)

---

## 9. Fase 6 — K8s Manifests (kubectl)

O Terraform gerencia addons e configuração. Os Deployments, Services e ServiceAccounts são aplicados via kubectl.

### 9.1. Preparar manifests para novo ambiente

```bash
mkdir -p k8s/${ENVIRONMENT}/inference k8s/${ENVIRONMENT}/process k8s/${ENVIRONMENT}/keda

# Copiar do dev como base
cp k8s/dev/namespace.yaml k8s/${ENVIRONMENT}/
cp k8s/dev/serviceaccount-*.yaml k8s/${ENVIRONMENT}/
cp k8s/dev/inference/deployment.yaml k8s/${ENVIRONMENT}/inference/
cp k8s/dev/inference/service.yaml k8s/${ENVIRONMENT}/inference/
cp k8s/dev/process/deployment.yaml k8s/${ENVIRONMENT}/process/
```

### 9.2. Atualizar referências nos manifests

Nos arquivos copiados, substituir:

```bash
# Account ID e região nos ECR image URIs
# De: 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest
# Para: <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/elo-fraud-inference-<ENVIRONMENT>:latest

# Labels de ambiente
# De: environment: dev
# Para: environment: <ENVIRONMENT>
```

### 9.3. Aplicar manifests (ordem importa)

```bash
# 1. Namespace (já criado pelo Terraform, mas o manifest define ResourceQuota e LimitRange)
kubectl apply -f k8s/${ENVIRONMENT}/namespace.yaml

# 2. ServiceAccounts + RBAC
kubectl apply -f k8s/${ENVIRONMENT}/serviceaccount-inference.yaml
kubectl apply -f k8s/${ENVIRONMENT}/serviceaccount-process.yaml

# 3. Deployments + Service
kubectl apply -f k8s/${ENVIRONMENT}/inference/deployment.yaml
kubectl apply -f k8s/${ENVIRONMENT}/inference/service.yaml
kubectl apply -f k8s/${ENVIRONMENT}/process/deployment.yaml
```

### 9.4. Verificar pods

```bash
kubectl get pods -n fraud-detection -o wide
kubectl get svc -n fraud-detection
kubectl get hpa -n fraud-detection
kubectl get scaledobject -n fraud-detection

# Logs do inference
kubectl logs -n fraud-detection -l app=inference --tail=50

# Logs do process
kubectl logs -n fraud-detection -l app=process --tail=50
```

### 9.5. Aguardar pods saudáveis

```bash
kubectl wait --for=condition=ready pod -l app=inference -n fraud-detection --timeout=300s
```

---

## 10. Fase 7 — Platform-Lambdas

### 10.1. Preparar o diretório

```bash
mkdir -p infra/environments/${ENVIRONMENT}/platform-lambdas
cp infra/environments/dev/platform-lambdas/*.tf infra/environments/${ENVIRONMENT}/platform-lambdas/
```

### 10.2. Configurar backend.tf

```hcl
terraform {
  backend "s3" {
    bucket       = "<TF_STATE_BUCKET>"
    key          = "<ENVIRONMENT>/platform-lambdas/terraform.tfstate"
    region       = "<TF_STATE_REGION>"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 10.3. Atualizar data.tf (3 remote states)

```hcl
data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/platform/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}

data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/foundation/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}

data "terraform_remote_state" "mlops" {
  backend = "s3"
  config = {
    bucket = "<TF_STATE_BUCKET>"
    key    = "<ENVIRONMENT>/mlops/terraform.tfstate"
    region = "<TF_STATE_REGION>"
  }
}
```

### 10.4. Configurar terraform.tfvars

```hcl
project_name   = "elo-fraud"
environment    = "<ENVIRONMENT>"
aws_region     = "<AWS_REGION>"
aws_account_id = "<ACCOUNT_ID>"

# IMPORTANTE: ARN da MLflow App (extraído na Fase 2, passo 5.6)
mlflow_tracking_uri = "<MLFLOW_APP_ARN>"

# Lambda: Register Best Model
lambda_register_best_model_timeout           = 300
lambda_register_best_model_memory_size       = 512
lambda_register_best_model_model_name        = "Felicidade"
lambda_register_best_model_metric_to_compare = "metrics.f1_oot"
lambda_register_best_model_best_model_run    = "best_estimator"
lambda_register_best_model_target_tag_key    = "stage"
lambda_register_best_model_target_tag        = "prod"

# Lambda: ETL Delta Filter
lambda_etl_timeout     = 900      # 15 min (max Lambda)
lambda_etl_memory_size = 10240    # 10 GB (pyarrow + deltalake)

# Lambda: Training Launcher
lambda_training_launcher_timeout         = 300
lambda_training_launcher_memory_size     = 512
lambda_training_launcher_experiment_name = "classificacao_6.0.0"
lambda_training_launcher_dataset_name    = "gold"
lambda_training_launcher_instance_type   = "ml.r5.4xlarge"   # 16 vCPU, 128GB RAM

# Data Lake prefixes
s3_prefix_landing_zone  = "landing_zone"
s3_prefix_training_zone = "training_zone"
```

### 10.5. Deploy

```bash
cd infra/environments/${ENVIRONMENT}/platform-lambdas

terraform init
terraform plan -out=tfplan
terraform apply tfplan

terraform output
```

**Recursos criados:**
- Lambda `elo-fraud-register-best-model-{env}` (container, trigger S3 sagemaker bucket)
- Lambda `elo-fraud-etl-delta-filter-{env}` (container, trigger S3 landing_zone/)
- Lambda `elo-fraud-training-launcher-{env}` (container, trigger S3 training_zone/*.parquet)
- S3 Bucket Notifications (2 triggers no data-processed bucket + 1 no sagemaker bucket)
- IAM Roles + Policies (AmazonSageMakerFullAccess, AmazonS3FullAccess)

---

## 11. Fase 8 — Validação E2E

### 11.1. Verificar infraestrutura

```bash
# EKS cluster
aws eks describe-cluster --name ${PROJECT_NAME}-cluster-${ENVIRONMENT} \
  --profile ${PROFILE} --region ${AWS_REGION} \
  --query 'cluster.status' --output text
# Esperado: ACTIVE

# Nodes
kubectl get nodes
# Esperado: Ready

# Pods
kubectl get pods -n fraud-detection
# Esperado: inference Running, process Running

# MLflow
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name ${PROJECT_NAME}-mlflow-${ENVIRONMENT} \
  --profile ${PROFILE} --region ${AWS_REGION} \
  --query 'TrackingServerStatus' --output text
# Esperado: Created

# Lambdas
for FN in register-best-model etl-delta-filter training-launcher; do
  echo "=== ${FN} ==="
  aws lambda get-function --function-name ${PROJECT_NAME}-${FN}-${ENVIRONMENT} \
    --profile ${PROFILE} --region ${AWS_REGION} \
    --query 'Configuration.State' --output text
done
# Esperado: Active

# Glue Jobs
aws glue get-jobs --profile ${PROFILE} --region ${AWS_REGION} \
  --query 'Jobs[].Name' --output text
```

### 11.2. Testar health check (via ALB)

```bash
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names ${PROJECT_NAME}-alb-${ENVIRONMENT} \
  --profile ${PROFILE} --region ${AWS_REGION} \
  --query 'LoadBalancers[0].DNSName' --output text)

curl http://${ALB_DNS}/health
# Esperado: {"status": "healthy"}
```

### 11.3. Testar scoring (via API Gateway)

```bash
API_URL=$(aws apigateway get-rest-apis --profile ${PROFILE} --region ${AWS_REGION} \
  --query "items[?name=='${PROJECT_NAME}-api-${ENVIRONMENT}'].id" --output text)

API_KEY=$(aws apigateway get-api-keys --profile ${PROFILE} --region ${AWS_REGION} \
  --include-values --query "items[0].value" --output text)

curl -X POST "https://${API_URL}.execute-api.${AWS_REGION}.amazonaws.com/v1/authorize-purchase" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "acctID": "test-123",
    "purchaseAmount": 100.00,
    "merchantCountryCode": "BRA"
  }'
```

### 11.4. Verificar pipeline ML (S3 triggers)

```bash
# Verificar S3 notifications configuradas
aws s3api get-bucket-notification-configuration \
  --bucket ${PROJECT_NAME}-data-processed-${ENVIRONMENT}-${ACCOUNT_ID} \
  --profile ${PROFILE} --region ${AWS_REGION} --output json

# Esperado: 2 LambdaFunctionConfigurations (landing_zone/ e training_zone/)
```

---

## 12. Referência — Arquitetura de Rede

```
Internet
    │
    ▼
API Gateway (Regional, público)
    │  POST /v1/authorize-purchase
    │  GET /health
    ▼
VPC Link
    │
    ▼
NLB (internal, private subnets)
    │  Port 80
    ▼
ALB (internal, private subnets)
    │  Port 80 → Target Group port 8000
    ▼
EKS Pods (inference, port 8000)
    │
    ├──► DynamoDB (feature lookup)
    ├──► MLflow (model loading)
    └──► SQS FIFO (async results) ──► EKS Pods (process)
                                          │
                                          ├──► DynamoDB (update)
                                          ├──► Firehose → S3 landing_zone/
                                          └──► Firehose → S3 inference_logs/
```

---

## 13. Referência — Recursos Criados

| Stack | Recurso | Quantidade | Custo Estimado |
|---|---|---|---|
| **Foundation** | VPC, Subnets, IGW, NAT GW | 1 | ~$32/mês (NAT) |
| | VPC Interface Endpoints | 9 | ~$130/mês |
| | VPC Gateway Endpoints (S3, DynamoDB) | 2 | Gratuito |
| | S3 Buckets | 7 | ~$1/mês |
| **MLOps** | MLflow Tracking Server (Small) | 1 | ~$30/mês |
| | SageMaker Studio Domain | 1 | Pay-per-use |
| | S3 MLflow Artifacts | 1 | ~$0.5/mês |
| **Platform** | EKS Cluster | 1 | ~$73/mês |
| | EKS Node Group (t3.medium) | 1-3 nós | ~$30-90/mês |
| | ALB (internal) | 1 | ~$16/mês |
| | NLB (internal) | 1 | ~$16/mês |
| | API Gateway | 1 | Pay-per-request |
| | DynamoDB (on-demand) | 1 | Pay-per-request |
| | SQS FIFO + DLQ | 2 | ~$0.5/mês |
| | Firehose Streams | 2 | Pay-per-GB |
| | Glue ETL Jobs | 2 | Pay-per-DPU-hour |
| | Athena | 1 | Pay-per-query |
| | ECR Repositories | 6 | ~$1/mês |
| | CloudWatch Dashboards | 2 | ~$6/mês |
| **Platform-K8s** | Helm Charts (4 addons) | 4 | Incluído no EKS |
| | HPA + KEDA ScaledObject | 2 | Incluído no EKS |
| | ConfigMaps + PDBs | 4 | Incluído no EKS |
| **Platform-Lambdas** | Lambda Functions (container) | 3 | Pay-per-invocation |

**Custo estimado total (dev)**: ~$270-350/mês

---

## 14. Troubleshooting

### Terraform init falha com "bucket not found"

```bash
# Verificar se o bootstrap foi executado
aws s3 ls s3://${TF_STATE_BUCKET} --profile ${PROFILE} --region ${AWS_REGION}
```

### EKS nodes não ficam Ready

```bash
kubectl describe nodes
# Verificar: Security Groups, NAT Gateway, IAM Node Role permissions
```

### Pods em CrashLoopBackOff

```bash
kubectl logs -n fraud-detection <POD_NAME> --previous
kubectl describe pod -n fraud-detection <POD_NAME>
# Causas comuns: imagem ECR não encontrada, ConfigMap ausente, permissões IAM
```

### Lambda falha com "ImageNotFound"

```bash
# Verificar se a imagem existe no ECR
aws ecr list-images --repository-name <REPO_NAME> \
  --profile ${PROFILE} --region ${AWS_REGION}
# Se vazio: voltar à Fase 4 e fazer docker build + push
```

### MLflow Tracking Server não conecta

```bash
# Verificar status
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name ${PROJECT_NAME}-mlflow-${ENVIRONMENT} \
  --profile ${PROFILE} --region ${AWS_REGION}
# Se "Stopped": iniciar via console ou CLI
```

### API Gateway retorna 403

```bash
# Verificar API Key
aws apigateway get-api-keys --profile ${PROFILE} --region ${AWS_REGION} --include-values
# Verificar Usage Plan associado ao stage
```

### SQS mensagens acumulando

```bash
kubectl get pods -n fraud-detection -l app=process
kubectl logs -n fraud-detection -l app=process --tail=100
# Verificar: pod running, DynamoDB/Firehose connectivity, IAM permissions
```

### Terraform lock stuck

```bash
# Listar locks
aws s3 ls "s3://${TF_STATE_BUCKET}/${ENVIRONMENT}/" --recursive --profile ${PROFILE} | grep '.tflock'

# Remover lock manual (CUIDADO: confirmar que ninguém está rodando terraform)
aws s3 rm "s3://${TF_STATE_BUCKET}/${ENVIRONMENT}/<STACK>/.terraform.tfstate.tflock" --profile ${PROFILE}
```
