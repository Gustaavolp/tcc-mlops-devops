# Deploy do Zero ao 100% - Elo Fraud Detection Platform

> **Responsavel**: Gustavo Liebl Pereira
> **Data de Criacao**: 2026-02-01
> **Versao**: 2.0.0
> **Ultima Atualizacao**: 2026-02-05

---

## Indice

1. [Pre-requisitos](#1-pre-requisitos)
2. [Visao Geral da Arquitetura](#2-visao-geral-da-arquitetura)
3. [Estrutura de Stacks e Dependencias](#3-estrutura-de-stacks-e-dependencias)
4. [FASE 1: Bootstrap - Configuracao Inicial](#4-fase-1-bootstrap---configuracao-inicial)
5. [FASE 2: Foundation - Rede e Storage Base](#5-fase-2-foundation---rede-e-storage-base)
6. [FASE 3: MLOps - Plataforma de Machine Learning](#6-fase-3-mlops---plataforma-de-machine-learning)
7. [FASE 4: Platform - Infraestrutura Principal](#7-fase-4-platform---infraestrutura-principal)
8. [FASE 5: Platform K8s - Recursos Kubernetes](#8-fase-5-platform-k8s---recursos-kubernetes)
9. [FASE 6: Platform Lambdas - Funcoes Serverless](#9-fase-6-platform-lambdas---funcoes-serverless)
10. [FASE 7: Build e Deploy dos Servicos](#10-fase-7-build-e-deploy-dos-servicos)
11. [FASE 8: Aplicar Manifests Kubernetes](#11-fase-8-aplicar-manifests-kubernetes)
12. [FASE 9: Validacao End-to-End](#12-fase-9-validacao-end-to-end)
13. [Troubleshooting](#13-troubleshooting)
14. [Rollback e Destruicao](#14-rollback-e-destruicao)
15. [Checklist Final](#15-checklist-final)

---

## 1. Pre-requisitos

### 1.1 Ferramentas Necessarias

```bash
# Versoes minimas requeridas
terraform --version   # >= 1.10.0
aws --version         # >= 2.15.0
kubectl version       # >= 1.30.0
helm version          # >= 3.14.0
docker --version      # >= 24.0.0
git --version         # >= 2.40.0
```

### 1.2 Instalacao das Ferramentas (Ubuntu/WSL)

```bash
# Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Docker
sudo apt-get install docker.io
sudo usermod -aG docker $USER
```

### 1.3 Configuracao AWS

```bash
# Configurar credenciais AWS
aws configure
# AWS Access Key ID: [SUA_ACCESS_KEY]
# AWS Secret Access Key: [SUA_SECRET_KEY]
# Default region name: us-east-1
# Default output format: json

# Verificar credenciais
aws sts get-caller-identity
```

**Output esperado:**
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "888577064416",
    "Arn": "arn:aws:iam::888577064416:user/seu-usuario"
}
```

### 1.4 Permissoes IAM Necessarias

O usuario/role precisa das seguintes permissoes (ou AdministratorAccess para simplificar):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "eks:*",
                "elasticloadbalancing:*",
                "apigateway:*",
                "s3:*",
                "dynamodb:*",
                "sqs:*",
                "firehose:*",
                "glue:*",
                "athena:*",
                "ecr:*",
                "iam:*",
                "lambda:*",
                "sagemaker:*",
                "logs:*",
                "cloudwatch:*",
                "kms:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### 1.5 Variaveis de Ambiente

```bash
# Definir variaveis de ambiente (adicionar ao ~/.bashrc)
export AWS_ACCOUNT_ID="888577064416"
export AWS_REGION_DEV="us-east-1"
export AWS_REGION_STAGING="sa-east-1"
export PROJECT_NAME="elo-fraud"
export TF_VAR_aws_account_id="888577064416"

# Recarregar
source ~/.bashrc
```

### 1.6 Clonar o Repositorio

```bash
cd ~/VSCode
git clone <URL_DO_REPOSITORIO> elocartoes-compraonline
cd elocartoes-compraonline
```

---

## 2. Visao Geral da Arquitetura

### 2.1 Diagrama de Arquitetura

```
+---------------------------------------------------------------------------------------------+
|                           FLUXO SINCRONO (Scoring) - SLA p95 < 500ms                        |
+---------------------------------------------------------------------------------------------+
|                                                                                             |
|   Elo --> API Gateway --> VPC Link --> NLB --> ALB (interno) --> EKS (inference)            |
|                                                        |                                    |
|                                                        +---> DynamoDB (consulta historico)  |
|                                                        +---> MLflow Model (SageMaker)       |
|                                                                    |                        |
|              <----------------------------------------------------+                         |
|                           Resposta: {score, fraud_label}                                    |
+---------------------------------------------------------------------------------------------+
|                          FLUXO ASSINCRONO (Feedback/Logging)                                |
+---------------------------------------------------------------------------------------------+
|                                                                                             |
|   Inference --> SQS FIFO --> EKS (process worker)                                           |
|                                       |                                                     |
|                                       +---> DynamoDB (update feature store)                 |
|                                       +---> Firehose --> S3 (data lake)                     |
|                                                                                             |
+---------------------------------------------------------------------------------------------+
```

### 2.2 Componentes por Stack

| Stack | Recursos | Tempo Estimado |
|-------|----------|----------------|
| Bootstrap | S3 State Bucket | 2 min |
| Foundation | VPC, Subnets, Endpoints, S3 Buckets | 15 min |
| MLOps | MLflow Server, SageMaker Studio | 20 min |
| Platform | EKS, ALB, NLB, API Gateway, DynamoDB, SQS, ECR (5 repos), Firehose, Glue, Athena | 30 min |
| Platform K8s | KEDA, ConfigMaps, TargetGroupBinding | 10 min |
| Platform Lambdas | Lambda register-best-model | 5 min |
| **TOTAL** | | **~90 min** |

---

## 3. Estrutura de Stacks e Dependencias

### 3.1 Grafo de Dependencias

```
                    Bootstrap (local state)
                           |
                           v
                    Foundation
                     /       \
                    v         v
                 MLOps    Platform
                           /    \
                          v      v
               Platform-K8s   Platform-Lambdas
```

### 3.2 Remote State Keys

```
s3://elo-fraud-terraform-state-888577064416-us-east-1/
├── dev/
│   ├── foundation/terraform.tfstate
│   ├── mlops/terraform.tfstate
│   ├── platform/terraform.tfstate
│   ├── platform-k8s/terraform.tfstate
│   └── platform-lambdas/terraform.tfstate
└── staging/
    └── (mesma estrutura)
```

### 3.3 Ordem de Deploy Obrigatoria

**IMPORTANTE**: As stacks DEVEM ser deployadas na ordem correta devido as dependencias via `terraform_remote_state`.

```bash
# DEV Environment
1. infra/bootstrap/                      # Primeiro (cria bucket de estado)
2. infra/environments/dev/foundation/    # Segundo (VPC, S3)
3. infra/environments/dev/mlops/         # Terceiro (depende de foundation)
4. infra/environments/dev/platform/      # Quarto (depende de foundation + mlops)
5. infra/environments/dev/platform-k8s/  # Quinto (depende de platform)
6. infra/environments/dev/platform-lambdas/  # Sexto (depende de platform)
```

---

## 4. FASE 1: Bootstrap - Configuracao Inicial

O Bootstrap cria o bucket S3 para armazenar o estado do Terraform.

### 4.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/bootstrap
```

### 4.2 Revisar Configuracao

```bash
# Verificar variaveis
cat terraform.tfvars.example
```

**Conteudo esperado:**
```hcl
# Regiao AWS centralizada para todos os states (opcional - padrao: us-east-1)
aws_region = "us-east-1"

# Nome do bucket S3 (obrigatorio)
# Formato recomendado: {project}-terraform-state-{account_id}-{region}
state_bucket_name = "elo-fraud-terraform-state-888577064416-us-east-1"

# Tags comuns para todos os recursos
tags = {
  Project   = "Elo Fraud Detection"
  ManagedBy = "Terraform"
  Owner     = "DevOps"
  Purpose   = "Terraform State Management"
}
```

### 4.3 Criar terraform.tfvars

```bash
cp terraform.tfvars.example terraform.tfvars

# Editar se necessario (ajustar account_id e region se diferente)
# nano terraform.tfvars
```

### 4.4 Inicializar e Aplicar

```bash
# Inicializar Terraform
terraform init

# Planejar mudancas
terraform plan -out=tfplan

# Aplicar (confirmar com 'yes')
terraform apply tfplan
```

### 4.5 Verificar Outputs

```bash
terraform output
```

**Output esperado:**
```
state_bucket_name = "elo-fraud-terraform-state-888577064416-us-east-1"
state_bucket_arn = "arn:aws:s3:::elo-fraud-terraform-state-888577064416-us-east-1"
state_bucket_region = "us-east-1"
```

### 4.6 Verificar no Console AWS

```bash
aws s3 ls | grep terraform-state
```

**Resultado:**
```
2026-02-01 10:00:00 elo-fraud-terraform-state-888577064416-us-east-1
```

---

## 5. FASE 2: Foundation - Rede e Storage Base

A Foundation cria a infraestrutura de rede (VPC) e os buckets S3 base.

### 5.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/foundation
```

### 5.2 Verificar Backend

```bash
cat backend.tf
```

**Conteudo:**
```hcl
terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "dev/foundation/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

### 5.3 Criar terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# =============================================================================
# TERRAFORM VARIABLES - FOUNDATION DEV (us-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

# VPC Configuration
vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# NAT Gateway - HABILITADO para pull de imagens de registries publicos
# Custo: ~$32/mes + data processing costs
# NOTA: VPC Endpoints continuam ativos para servicos AWS (ECR, SQS, etc.)
# NAT Gateway e usado apenas para trafego sem VPC Endpoint (registry.k8s.io, ghcr.io)
enable_nat_gateway = true
single_nat_gateway = true  # Usar apenas 1 NAT Gateway (economia de custos)

# VPC Gateway Endpoints (S3, DynamoDB - gratuitos)
enable_vpc_endpoints = true

# VPC Interface Endpoints (substituem NAT Gateway para servicos AWS)
# Endpoints: ECR API/DKR, CloudWatch Logs, SQS, STS, EC2, SageMaker API/Runtime, Firehose
# Custo: ~$129.60/mes (9 endpoints x $7.20 x 2 AZs)
enable_interface_endpoints = true

# S3 Configuration
s3_enable_versioning          = true
s3_force_destroy              = true  # Apenas para dev - permite deletar buckets com objetos
s3_raw_retention_days         = 30    # Dias antes de mover dados raw para Glacier
s3_processed_retention_days   = 90    # Dias antes de mover dados processed para Glacier
s3_logs_retention_days        = 90    # Dias antes de mover logs para Glacier
s3_models_retention_enabled   = false # Desabilitado - modelos sao versionados no MLflow
s3_enable_intelligent_tiering = true  # Otimizacao automatica de custos

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Foundation"
  Region      = "us-east-1"
}
EOF
```

### 5.4 Inicializar e Aplicar

```bash
# Inicializar (baixa modulos e configura backend)
terraform init

# Validar sintaxe
terraform validate

# Planejar mudancas
terraform plan -out=tfplan

# Revisar o plan (deve criar ~60+ recursos)
# Recursos principais:
# - aws_vpc
# - aws_subnet (4x: 2 publicas + 2 privadas)
# - aws_internet_gateway
# - aws_nat_gateway (1x se single_nat_gateway=true)
# - aws_eip (para NAT Gateway)
# - aws_route_table (3x: public + private por AZ)
# - aws_vpc_endpoint (11x: S3, DynamoDB, ECR, Logs, SQS, STS, EC2, SageMaker, Firehose)
# - aws_security_group (2x: ALB + VPC Endpoints)
# - aws_s3_bucket (7x: raw, processed, models, logs, resources, reports-promotion, reports-statistics)
# - aws_s3_bucket_lifecycle_configuration
# - aws_s3_bucket_versioning

# Aplicar
terraform apply tfplan
```

### 5.5 Verificar Outputs

```bash
terraform output
```

**Outputs importantes:**
```
vpc_id = "vpc-0abc123def456789"
vpc_cidr = "10.0.0.0/16"
public_subnet_ids = ["subnet-pub1", "subnet-pub2"]
private_subnet_ids = ["subnet-priv1", "subnet-priv2"]
security_group_alb_id = "sg-0abc123"
security_group_vpc_endpoints_id = "sg-0def456"
nat_gateway_ids = ["nat-xxx"]
nat_gateway_public_ips = ["x.x.x.x"]

# S3 Buckets (7 total)
s3_raw_bucket_id = "elo-fraud-data-raw-dev-888577064416"
s3_processed_bucket_id = "elo-fraud-data-processed-dev-888577064416"
s3_models_bucket_id = "elo-fraud-models-dev-888577064416"
s3_logs_bucket_id = "elo-fraud-logs-dev-888577064416"
s3_resources_bucket_id = "elo-fraud-resources-dev-888577064416"
s3_reports_promotion_bucket_id = "elo-fraud-reports-promotion-dev-888577064416"
s3_reports_statistics_bucket_id = "elo-fraud-reports-statistics-dev-888577064416"
```

### 5.6 Verificar Recursos Criados

```bash
# VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=*elo-fraud*" --query 'Vpcs[*].[VpcId,CidrBlock]' --output table

# Subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone]' --output table

# S3 Buckets
aws s3 ls | grep elo-fraud
```

---

## 6. FASE 3: MLOps - Plataforma de Machine Learning

O MLOps cria o MLflow Tracking Server e o SageMaker Studio.

### 6.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/mlops
```

### 6.2 Criar terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# =============================================================================
# TERRAFORM VARIABLES - MLOPS DEV (us-east-1)
# =============================================================================

# General
project_name       = "elo-fraud"
environment        = "dev"
mlflow_environment = "dev"
aws_region         = "us-east-1"
aws_account_id     = "888577064416"

# MLflow Configuration
tracking_server_size            = "Small"     # Small, Medium ou Large
mlflow_version                  = "3.0"       # Versao do MLflow
weekly_maintenance_window_start = "Sun:03:00" # Domingo 03:00 UTC (00:00 BRT)
log_retention_days              = 7           # Dias de retencao dos logs

# SageMaker Studio Configuration
# NOTA: Idle shutdown esta sempre habilitado (60 min de inatividade)
# NOTA: Modo de rede e sempre PublicInternetOnly
default_notebook_instance_type = "ml.t3.medium"
idle_timeout_in_minutes        = 60
sagemaker_user_profile_name    = "elo-fraud-ml-user"

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "MLOps"
  Region      = "us-east-1"
}
EOF
```

### 6.3 Verificar Data Sources

```bash
cat data.tf
```

**Deve conter:**
```hcl
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 6.4 Inicializar e Aplicar

```bash
terraform init
terraform validate
terraform plan -out=tfplan

# Recursos criados:
# - aws_sagemaker_mlflow_tracking_server
# - aws_s3_bucket (mlflow artifacts)
# - aws_sagemaker_domain
# - aws_sagemaker_user_profile
# - aws_iam_role (3x)
# - aws_cloudwatch_log_group (2x)

terraform apply tfplan
```

### 6.5 Verificar Outputs

```bash
terraform output
```

**Outputs importantes:**
```
mlflow_tracking_server_name = "elo-fraud-mlflow-dev"
mlflow_tracking_server_arn = "arn:aws:sagemaker:us-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-dev"
mlflow_tracking_uri = "aws://sagemaker/elo-fraud-mlflow-dev"
mlflow_tracking_server_url = "https://mlflow-dev.xxxxxxxx.us-east-1.sagemaker.aws"
mlflow_artifact_bucket_name = "elo-fraud-mlflow-artifacts-dev-888577064416"
studio_domain_id = "d-xxxxxxxxxx"
studio_domain_url = "https://d-xxxxxxxxxx.studio.us-east-1.sagemaker.aws"
studio_execution_role_arn = "arn:aws:iam::888577064416:role/elo-fraud-studio-execution-role-dev"
```

### 6.6 Verificar no Console

```bash
# MLflow Tracking Server
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name $(terraform output -raw mlflow_tracking_server_name)

# SageMaker Studio Domain
aws sagemaker describe-domain \
  --domain-id $(terraform output -raw studio_domain_id)
```

---

## 7. FASE 4: Platform - Infraestrutura Principal

A Platform cria a infraestrutura principal: EKS, ALB, NLB, API Gateway, DynamoDB, SQS, ECR, Firehose, Glue.

### 7.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform
```

### 7.2 Criar terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# =============================================================================
# TERRAFORM VARIABLES - PLATFORM DEV (us-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

# VPC Configuration (referencia)
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# EKS Configuration
cluster_version     = "1.32"
node_instance_types = ["t3.medium"] # 2 vCPU, 4GB RAM - otimizado para custo
node_min_size       = 2             # 2 nodes para HA durante deploys
node_max_size       = 4             # Headroom para picos de carga
node_desired_size   = 2             # Baseline para testes de carga moderados

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Platform"
  Region      = "us-east-1"
}

# -----------------------------------------------------------------------------
# API Gateway Configuration
# -----------------------------------------------------------------------------
api_keys = {
  "elo-backend" = {
    enabled     = true
    description = "API Key para backend Elo - DEV"
  }
  "testing" = {
    enabled     = true
    description = "API Key para testes automatizados - DEV"
  }
}

# -----------------------------------------------------------------------------
# SQS Configuration
# -----------------------------------------------------------------------------
sqs_visibility_timeout_seconds = 300     # 5 minutos para processar
sqs_message_retention_seconds  = 1209600 # 14 dias
sqs_receive_wait_time_seconds  = 20      # Long polling
sqs_max_receive_count          = 3       # 3 tentativas antes de ir para DLQ

# -----------------------------------------------------------------------------
# Lambda ETL Delta Filter Configuration
# -----------------------------------------------------------------------------
lambda_etl_delta_table_prefix = "transformed_zone"
lambda_etl_output_prefix      = "training_zone"
lambda_etl_date_column        = "dt_transaction_datetime"
lambda_etl_n_months_oot       = "3"     # Meses para periodo OOT (Out-of-Time)
lambda_etl_n_months_test      = "1"     # Meses para periodo de teste
lambda_etl_batch_size         = "20000"

# -----------------------------------------------------------------------------
# ALB Configuration
# -----------------------------------------------------------------------------
alb_target_group_port     = 8000 # Porta do servico inference
alb_deregistration_delay  = 30   # Segundos para deregistration
alb_health_check_interval = 30   # Segundos entre health checks
alb_health_check_timeout  = 5    # Segundos de timeout
alb_healthy_threshold     = 2    # Checks para considerar saudavel
alb_unhealthy_threshold   = 3    # Checks para considerar nao saudavel
alb_listener_port         = 80   # Porta do listener HTTP
alb_idle_timeout          = 60   # Idle timeout do ALB

# -----------------------------------------------------------------------------
# NLB Configuration
# -----------------------------------------------------------------------------
nlb_target_port           = 80 # Porta do ALB (target do NLB)
nlb_listener_port         = 80 # Porta que o VPC Link acessa
nlb_health_check_interval = 30 # Segundos entre health checks
nlb_health_check_timeout  = 10 # Segundos de timeout
nlb_healthy_threshold     = 3  # Checks para considerar saudavel
nlb_unhealthy_threshold   = 3  # Checks para considerar nao saudavel

# -----------------------------------------------------------------------------
# Firehose Configuration
# -----------------------------------------------------------------------------
firehose_buffer_size_mb          = 1  # MB (minimo suportado) - entrega rapida
firehose_buffer_interval_seconds = 60 # Segundos (minimo suportado)

# -----------------------------------------------------------------------------
# API Gateway Extended Configuration
# -----------------------------------------------------------------------------
api_gateway_log_retention_days              = 30     # 30 dias de retencao
api_gateway_usage_plan_quota_limit          = 100000 # 100K requests/mes
api_gateway_usage_plan_throttle_burst_limit = 1000   # Burst por API Key
api_gateway_usage_plan_throttle_rate_limit  = 500    # Rate por API Key

# -----------------------------------------------------------------------------
# Lambda ETL Extended Configuration
# -----------------------------------------------------------------------------
lambda_etl_log_retention_days = 14    # Dias de retencao dos logs
lambda_etl_timeout            = 900   # 15 minutos - processamento Delta Lake
lambda_etl_memory_size        = 10240 # 10 GB - necessario para pyarrow/deltalake

# -----------------------------------------------------------------------------
# Security Configuration
# -----------------------------------------------------------------------------
inference_service_port = 8000 # Porta do servico inference (ALB -> EKS pods)

# -----------------------------------------------------------------------------
# Athena Configuration
# -----------------------------------------------------------------------------
athena_bytes_scanned_limit = 10737418240 # 10 GB limite por query
athena_force_destroy       = true        # Permitir deletar bucket em dev

# -----------------------------------------------------------------------------
# SQS Alarm Configuration
# -----------------------------------------------------------------------------
sqs_alarm_queue_depth_threshold = 1000 # Mensagens na fila para alarme
sqs_alarm_age_threshold_seconds = 600  # 10 minutos - idade maxima da mensagem

# -----------------------------------------------------------------------------
# API Gateway Stage Configuration
# -----------------------------------------------------------------------------
api_gateway_stage_name                 = "v1"   # Stage do API Gateway
api_gateway_stage_throttle_burst_limit = 5000   # Burst limit do stage
api_gateway_stage_throttle_rate_limit  = 10000  # Rate limit do stage

# -----------------------------------------------------------------------------
# Glue ETL Configuration
# -----------------------------------------------------------------------------
glue_version           = "5.0"  # Versao do AWS Glue
glue_worker_type       = "G.1X" # Tipo de worker (G.1X = 4 vCPU, 16GB)
glue_number_of_workers = 10     # Workers para processamento paralelo
glue_job_timeout       = 480    # Timeout em minutos (8 horas)
glue_max_retries       = 0      # Sem retries automaticos

# Glue Job Names e Schedule
glue_training_job_name = "job_training_test_1"   # Job 1: merge landing -> transformed
glue_enrich_job_name   = "job_backfill_enrich"   # Job 2: feature engineering
glue_training_schedule = "cron(0 8 ? * SUN *)"   # Domingo 08:00 UTC (05:00 BRT)

# -----------------------------------------------------------------------------
# DynamoDB Schema Configuration
# -----------------------------------------------------------------------------
dynamodb_hash_key  = "acctID"                # Partition key: Account ID
dynamodb_range_key = "threeDSServerTransID"  # Sort key: 3DS Server Transaction ID

# -----------------------------------------------------------------------------
# Data Lake S3 Prefixes
# -----------------------------------------------------------------------------
s3_prefix_landing_zone     = "landing_zone"     # Dados brutos do Firehose
s3_prefix_transformed_zone = "transformed_zone" # Dados processados (Delta Lake)
s3_prefix_inference_logs   = "inference_logs"   # Logs de inferencia
EOF
```

### 7.3 Inicializar e Aplicar

```bash
terraform init
terraform validate
terraform plan -out=tfplan

# Este plan cria MUITOS recursos (~100+):
# - EKS Cluster + Node Group
# - ALB + Target Group + Listener
# - NLB + Target Group + Attachment
# - API Gateway + VPC Link + Resources + Methods + Deployment
# - DynamoDB Table
# - SQS FIFO + DLQ
# - ECR Repositories (5x: inference, process, model, best-model-register, etl-delta-filter)
# - Firehose Streams (2x)
# - Glue Database + Tables + Jobs
# - Athena Workgroup + Database + Tables
# - Lambda ETL Delta Filter
# - Bedrock Agent Role
# - IAM Roles (varios)
# - Security Groups
# - CloudWatch Dashboards + Alarms

# ATENCAO: Este apply demora ~30 minutos (EKS e ALB sao lentos)
terraform apply tfplan
```

### 7.4 Monitorar Progresso

```bash
# Em outro terminal, monitorar criacao do EKS
watch -n 10 "aws eks describe-cluster --name elo-fraud-cluster-dev --query 'cluster.status'"

# Status esperado: CREATING -> ACTIVE
```

### 7.5 Verificar Outputs

```bash
terraform output
```

**Outputs importantes:**
```
eks_cluster_name = "elo-fraud-cluster-dev"
eks_cluster_endpoint = "https://XXXXX.gr7.us-east-1.eks.amazonaws.com"
eks_cluster_certificate_authority_data = "LS0tLS1..."

alb_dns_name = "elo-fraud-alb-dev-XXXXX.us-east-1.elb.amazonaws.com"
alb_target_group_arn = "arn:aws:elasticloadbalancing:..."

nlb_dns_name = "elo-fraud-nlb-dev-XXXXX.elb.us-east-1.amazonaws.com"
nlb_arn = "arn:aws:elasticloadbalancing:..."

api_gateway_invoke_url = "https://XXXXX.execute-api.us-east-1.amazonaws.com/v1"
api_gateway_api_keys = <sensitive>  # Use: terraform output -json api_gateway_api_keys

dynamodb_table_name = "elo-fraud-customer-recent-tx-dev"
sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo"

ecr_inference_repository_url = "888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev"
ecr_process_repository_url = "888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-process-dev"
ecr_model_repository_url = "888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-model-dev"
ecr_register_best_model_url = "888577064416.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev"
ecr_etl_delta_filter_url = "888577064416.dkr.ecr.us-east-1.amazonaws.com/etl-delta-filter-dev"
```

### 7.6 Configurar kubectl

```bash
# Configurar kubeconfig
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1

# Verificar conexao
kubectl cluster-info

# Verificar nodes
kubectl get nodes
```

**Output esperado:**
```
NAME                          STATUS   ROLES    AGE   VERSION
ip-10-0-11-xxx.ec2.internal   Ready    <none>   5m    v1.32.0-eks-xxxxx
ip-10-0-12-xxx.ec2.internal   Ready    <none>   5m    v1.32.0-eks-xxxxx
```

### 7.7 Verificar Recursos AWS

```bash
# EKS Cluster
aws eks describe-cluster --name elo-fraud-cluster-dev --query 'cluster.[name,status,version]' --output table

# ALB
aws elbv2 describe-load-balancers --names elo-fraud-alb-dev --query 'LoadBalancers[*].[LoadBalancerName,State.Code,DNSName]' --output table

# DynamoDB
aws dynamodb describe-table --table-name elo-fraud-customer-recent-tx-dev --query 'Table.[TableName,TableStatus,ItemCount]' --output table

# SQS
aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo --attribute-names All

# ECR
aws ecr describe-repositories --query 'repositories[?contains(repositoryName, `elo-fraud`)].repositoryName' --output table
```

---

## 8. FASE 5: Platform K8s - Recursos Kubernetes

O Platform K8s cria os recursos Kubernetes gerenciados pelo Terraform: KEDA, ConfigMaps, TargetGroupBinding.

### 8.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform-k8s
```

### 8.2 Criar terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# =============================================================================
# TERRAFORM VARIABLES - PLATFORM K8S DEV (us-east-1)
# =============================================================================
# NOTA: Esta stack usa valores hardcoded para HPA/KEDA nos arquivos .tf
# Os valores de scaling sao definidos em:
# - autoscaling.tf (HPA para inference)
# - addons.tf (KEDA para process)
# Se precisar ajustar, edite diretamente esses arquivos.
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Platform-K8s"
  Region      = "us-east-1"
}
EOF
```

> **NOTA**: Os valores de HPA e KEDA sao configurados diretamente nos arquivos Terraform:
> - HPA (Inference): `infra/environments/dev/platform-k8s/autoscaling.tf`
> - KEDA (Process): `k8s/dev/keda/process-scaledobject.yaml`

### 8.3 Inicializar e Aplicar

```bash
terraform init
terraform validate
terraform plan -out=tfplan

# Recursos criados:
# - kubernetes_namespace (fraud-detection)
# - helm_release (aws-load-balancer-controller)
# - helm_release (keda)
# - kubernetes_deployment (cluster-autoscaler)
# - kubernetes_config_map (inference-config)
# - kubernetes_config_map (process-config)
# - kubernetes_manifest (TargetGroupBinding)
# - kubernetes_horizontal_pod_autoscaler (inference)
# - kubectl_manifest (KEDA ScaledObject)

terraform apply tfplan
```

### 8.4 Verificar Recursos Kubernetes

```bash
# Namespace
kubectl get namespace fraud-detection

# ConfigMaps
kubectl get configmap -n fraud-detection
kubectl describe configmap inference-config -n fraud-detection
kubectl describe configmap process-config -n fraud-detection

# KEDA
kubectl get pods -n keda
kubectl get scaledobject -n fraud-detection

# AWS Load Balancer Controller
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# TargetGroupBinding
kubectl get targetgroupbinding -n fraud-detection
```

---

## 9. FASE 6: Platform Lambdas - Funcoes Serverless

O Platform Lambdas cria as Lambda Functions.

### 9.1 Navegar para o Diretorio

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform-lambdas
```

### 9.2 Criar terraform.tfvars

```bash
cat > terraform.tfvars << 'EOF'
# =============================================================================
# TERRAFORM VARIABLES - PLATFORM LAMBDAS DEV (us-east-1)
# =============================================================================

# General
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

# =============================================================================
# MLflow Configuration
# =============================================================================
# NOTA: O MLflow App (arn:...:mlflow-app/app-XXX) e diferente do MLflow Tracking
# Server (arn:...:mlflow-tracking-server/nome) gerenciado pelo Terraform.
#
# O MLflow App e:
# - Criado AUTOMATICAMENTE pelo SageMaker Studio Domain
# - Serverless (sem sizing, auto-scaling)
# - Sem custo adicional
# - NAO possui recurso Terraform para gerenciamento
#
# O ARN e estavel apos a criacao do Studio Domain e nao muda.
# Se o Studio Domain for recriado, este ARN precisara ser atualizado.
# Para obter o ARN, acesse: SageMaker Console > Studio > Seu Domain > Apps
# =============================================================================
mlflow_tracking_uri = "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-XXXXXXXXXX"

# Tags
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Platform-Lambdas"
  Region      = "us-east-1"
}

# =============================================================================
# Lambda Register Best Model Configuration
# =============================================================================
lambda_register_best_model_timeout     = 300 # 5 minutos
lambda_register_best_model_memory_size = 512 # MB

# MLflow Model Registry Configuration
lambda_register_best_model_model_name        = "Felicidade"        # Nome do modelo no registry
lambda_register_best_model_metric_to_compare = "metrics.f1_oot"    # Metrica para comparacao
lambda_register_best_model_best_model_run    = "best_estimator"    # Nome do run
lambda_register_best_model_target_tag_key    = "stage"             # Chave da tag
lambda_register_best_model_target_tag        = "prod"              # Valor da tag
EOF
```

> **IMPORTANTE**: Atualize o `mlflow_tracking_uri` com o ARN correto do MLflow App.
> Para obter o ARN, apos criar a stack MLOps, acesse o console do SageMaker.

### 9.3 Build da Imagem Lambda (Pre-requisito)

```bash
# A Lambda usa imagem container do ECR
# Primeiro, fazer build e push da imagem

cd /home/gustavoliebl/VSCode/elocartoes-compraonline/lambdas/register-best-model

# Login ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t best-model-register-dev:latest .

# Tag (NOTA: repositorio ECR eh "best-model-register-dev", sem prefixo elo-fraud)
docker tag best-model-register-dev:latest 888577064416.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev:latest

# Push
docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev:latest
```

### 9.4 Inicializar e Aplicar

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform-lambdas

terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

### 9.5 Verificar Lambda

```bash
# Listar Lambdas
aws lambda list-functions --query 'Functions[?contains(FunctionName, `elo-fraud`)].FunctionName' --output table

# Detalhes da Lambda
aws lambda get-function --function-name elo-fraud-register-best-model-dev
```

---

## 10. FASE 7: Build e Deploy dos Servicos

Agora vamos buildar e fazer push das imagens Docker dos servicos.

### 10.1 Login no ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-1.amazonaws.com
```

### 10.2 Build do Servico Inference

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/services/inference

# Build
docker build -t elo-fraud-inference-dev:latest .

# Tag (usar output do Terraform para URL exato)
docker tag elo-fraud-inference-dev:latest 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest

# Push
docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest

# Verificar
aws ecr describe-images --repository-name elo-fraud-inference-dev --query 'imageDetails[*].[imageTags,imagePushedAt]' --output table
```

### 10.3 Build do Servico Process

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/services/process

# Build
docker build -t elo-fraud-process-dev:latest .

# Tag
docker tag elo-fraud-process-dev:latest 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-process-dev:latest

# Push
docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-process-dev:latest

# Verificar
aws ecr describe-images --repository-name elo-fraud-process-dev --query 'imageDetails[*].[imageTags,imagePushedAt]' --output table
```

### 10.4 Script Automatizado de Build

```bash
#!/bin/bash
# save as: scripts/build-and-push.sh

set -e

ACCOUNT_ID="888577064416"
REGION="us-east-1"
ENV="dev"
PROJECT="elo-fraud"

# Login
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Inference
echo "Building inference..."
cd services/inference
docker build -t $PROJECT-inference-$ENV:latest .
docker tag $PROJECT-inference-$ENV:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT-inference-$ENV:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT-inference-$ENV:latest

# Process
echo "Building process..."
cd ../process
docker build -t $PROJECT-process-$ENV:latest .
docker tag $PROJECT-process-$ENV:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT-process-$ENV:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$PROJECT-process-$ENV:latest

# Lambda - Best Model Register (NOTA: sem prefixo elo-fraud)
echo "Building lambda register-best-model..."
cd ../../lambdas/register-best-model
docker build -t best-model-register-$ENV:latest .
docker tag best-model-register-$ENV:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/best-model-register-$ENV:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/best-model-register-$ENV:latest

echo "Done!"
```

---

## 11. FASE 8: Aplicar Manifests Kubernetes

Agora vamos aplicar os manifests Kubernetes (Deployments, Services, etc).

### 11.1 Verificar Conexao com Cluster

```bash
kubectl cluster-info
kubectl get nodes
```

### 11.2 Aplicar Manifests na Ordem Correta

```bash
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/k8s/dev

# 1. Namespace (se nao foi criado pelo Terraform)
kubectl apply -f namespace.yaml

# 2. Service Accounts
kubectl apply -f serviceaccount-inference.yaml
kubectl apply -f serviceaccount-process.yaml

# 3. Inference Deployment e Service
kubectl apply -f inference/deployment.yaml
kubectl apply -f inference/service.yaml

# NOTA: HPA ja foi criado pelo Terraform (platform-k8s)
# Apenas para referencia:
# kubectl apply -f inference/hpa.yaml

# 4. Process Deployment
kubectl apply -f process/deployment.yaml

# NOTA: KEDA ScaledObject ja foi criado pelo Terraform
# Apenas para referencia:
# kubectl apply -f keda/process-scaledobject.yaml
```

### 11.3 Verificar Deployments

```bash
# Pods
kubectl get pods -n fraud-detection -w

# Aguardar todos os pods estarem Running
# NAME                         READY   STATUS    RESTARTS   AGE
# inference-xxxxx-xxxxx        1/1     Running   0          2m
# inference-xxxxx-xxxxx        1/1     Running   0          2m
# process-xxxxx-xxxxx          1/1     Running   0          1m

# Logs do Inference
kubectl logs -n fraud-detection -l app=inference --tail=50

# Logs do Process
kubectl logs -n fraud-detection -l app=process --tail=50
```

### 11.4 Verificar Service

```bash
kubectl get service -n fraud-detection

# NAME        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
# inference   ClusterIP   172.20.xx.xx    <none>        8000/TCP   5m
```

### 11.5 Verificar HPA e KEDA

```bash
# HPA (Inference)
kubectl get hpa -n fraud-detection
kubectl describe hpa inference-hpa -n fraud-detection

# KEDA ScaledObject (Process)
kubectl get scaledobject -n fraud-detection
kubectl describe scaledobject process-scaledobject -n fraud-detection
```

### 11.6 Verificar TargetGroupBinding

```bash
kubectl get targetgroupbinding -n fraud-detection
kubectl describe targetgroupbinding inference-tgb -n fraud-detection

# Verificar se pods foram registrados no ALB Target Group
aws elbv2 describe-target-health --target-group-arn $(terraform -chdir=/home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform output -raw alb_target_group_arn)
```

**Output esperado:**
```json
{
    "TargetHealthDescriptions": [
        {
            "Target": {"Id": "10.0.11.xxx", "Port": 8000},
            "HealthCheckPort": "8000",
            "TargetHealth": {"State": "healthy"}
        },
        {
            "Target": {"Id": "10.0.12.xxx", "Port": 8000},
            "HealthCheckPort": "8000",
            "TargetHealth": {"State": "healthy"}
        }
    ]
}
```

---

## 12. FASE 9: Validacao End-to-End

### 12.1 Testar Health Check (Interno)

```bash
# Port-forward para testar localmente
kubectl port-forward -n fraud-detection svc/inference 8000:8000 &

# Testar health
curl http://localhost:8000/health

# Output esperado:
# {"status": "healthy"}

# Matar port-forward
pkill -f "port-forward"
```

### 12.2 Testar via API Gateway

```bash
# Obter URL e API Key do Terraform
cd /home/gustavoliebl/VSCode/elocartoes-compraonline/infra/environments/dev/platform

API_URL=$(terraform output -raw api_gateway_invoke_url)
# API Keys sao retornadas como mapa - extrair a key "elo-backend"
API_KEY=$(terraform output -json api_gateway_api_keys | jq -r '.["elo-backend"]')

# Testar health (sem API Key)
curl -s "${API_URL}/health" | jq .

# Output esperado:
# {"status": "healthy"}

# Testar scoring (com API Key)
curl -s -X POST "${API_URL}/authorize-purchase" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "threeDSServerTransID": "test-001",
    "purchaseAmount": "100000",
    "purchaseCurrency": "986",
    "purchaseExponent": "2",
    "purchaseDate": "20260201120000",
    "cardHolderDocument": "12345678901"
  }' | jq .

# Output esperado:
# {
#   "transaction_id": "test-001",
#   "score": 0.23,
#   "fraud_label": 0
# }
```

### 12.3 Verificar Fluxo Assincrono (SQS -> Process -> DynamoDB)

```bash
# Verificar mensagens na fila SQS
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# Verificar DynamoDB (deve ter o registro da transacao)
# NOTA: Hash key = acctID, Range key = threeDSServerTransID
aws dynamodb query \
  --table-name elo-fraud-customer-recent-tx-dev \
  --key-condition-expression "acctID = :acc" \
  --expression-attribute-values '{":acc": {"S": "12345678901"}}' \
  --output table

# Verificar Firehose (dados devem chegar no S3 apos ~1 minuto)
# NOTA: Use o output s3_processed_bucket_id da Foundation para o nome correto
aws s3 ls s3://elo-fraud-data-processed-dev-888577064416/landing_zone/ --recursive
```

### 12.4 Verificar Logs CloudWatch

```bash
# Logs do Inference
aws logs tail /aws/eks/elo-fraud-cluster-dev/inference --follow

# Logs do Process
aws logs tail /aws/eks/elo-fraud-cluster-dev/process --follow

# Logs da API Gateway
aws logs tail /aws/apigateway/elo-fraud-api-dev --follow
```

### 12.5 Testar Auto-Scaling

```bash
# Enviar multiplas requests para testar HPA
for i in {1..100}; do
  curl -s -X POST "${API_URL}/authorize-purchase" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${API_KEY}" \
    -d "{\"threeDSServerTransID\": \"load-test-$i\", \"purchaseAmount\": \"10000\", \"purchaseCurrency\": \"986\", \"cardHolderDocument\": \"12345678901\"}" &
done
wait

# Observar HPA
watch kubectl get hpa -n fraud-detection

# Observar pods
watch kubectl get pods -n fraud-detection
```

---

## 13. Troubleshooting

### 13.1 Problemas Comuns

#### Erro: "Error: error configuring Terraform AWS Provider: no valid credential sources"

```bash
# Verificar credenciais
aws sts get-caller-identity

# Se falhar, reconfigurar
aws configure
```

#### Erro: "Error: Kubernetes cluster unreachable"

```bash
# Atualizar kubeconfig
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1

# Verificar contexto
kubectl config current-context
```

#### Erro: "Error: ImagePullBackOff"

```bash
# Verificar se imagem existe no ECR
aws ecr describe-images --repository-name elo-fraud-inference-dev

# Verificar logs do pod
kubectl describe pod -n fraud-detection <POD_NAME>

# Verificar se Node IAM Role tem permissao ECR
aws iam list-attached-role-policies --role-name elo-fraud-eks-node-role-dev
```

#### Erro: "CrashLoopBackOff"

```bash
# Verificar logs do container
kubectl logs -n fraud-detection <POD_NAME> --previous

# Verificar eventos
kubectl describe pod -n fraud-detection <POD_NAME>

# Verificar recursos (OOMKilled?)
kubectl top pod -n fraud-detection
```

#### Erro: "TargetGroup health check failing"

```bash
# Verificar se inference esta respondendo
kubectl exec -n fraud-detection <INFERENCE_POD> -- curl -s localhost:8000/health

# Verificar Security Group
# ALB SG deve permitir trafego para pods na porta 8000

# Verificar Target Group
aws elbv2 describe-target-health --target-group-arn <TG_ARN>
```

### 13.2 Comandos de Diagnostico

```bash
# Estado geral do cluster
kubectl get all -n fraud-detection

# Eventos recentes
kubectl get events -n fraud-detection --sort-by='.lastTimestamp'

# Descrever recursos
kubectl describe deployment inference -n fraud-detection
kubectl describe deployment process -n fraud-detection

# Logs em tempo real
kubectl logs -n fraud-detection -l app=inference -f
kubectl logs -n fraud-detection -l app=process -f

# Metricas
kubectl top nodes
kubectl top pods -n fraud-detection

# KEDA diagnostico
kubectl logs -n keda -l app=keda-operator --tail=100
```

### 13.3 Reset de Recursos

```bash
# Restart de deployment
kubectl rollout restart deployment inference -n fraud-detection
kubectl rollout restart deployment process -n fraud-detection

# Deletar pods (serao recriados)
kubectl delete pods -n fraud-detection --all

# Force pull de nova imagem
kubectl set image deployment/inference inference=888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev:latest -n fraud-detection
```

---

## 14. Rollback e Destruicao

### 14.1 Rollback de Deployment

```bash
# Ver historico de revisoes
kubectl rollout history deployment inference -n fraud-detection

# Rollback para revisao anterior
kubectl rollout undo deployment inference -n fraud-detection

# Rollback para revisao especifica
kubectl rollout undo deployment inference -n fraud-detection --to-revision=2
```

### 14.2 Destruicao Completa (CUIDADO!)

**ATENCAO**: Execute na ordem INVERSA do deploy!

```bash
# 1. Remover manifests Kubernetes
kubectl delete -f k8s/dev/process/deployment.yaml
kubectl delete -f k8s/dev/inference/deployment.yaml
kubectl delete -f k8s/dev/inference/service.yaml
kubectl delete -f k8s/dev/serviceaccount-*.yaml
kubectl delete -f k8s/dev/namespace.yaml

# 2. Destruir Platform Lambdas
cd infra/environments/dev/platform-lambdas
terraform destroy -auto-approve

# 3. Destruir Platform K8s
cd ../platform-k8s
terraform destroy -auto-approve

# 4. Destruir Platform
cd ../platform
terraform destroy -auto-approve
# ATENCAO: Isso demora ~20 minutos (EKS, ALB, VPC Link)

# 5. Destruir MLOps
cd ../mlops
terraform destroy -auto-approve

# 6. Destruir Foundation
cd ../foundation
terraform destroy -auto-approve
# ATENCAO: Buckets S3 com dados NAO serao deletados (lifecycle prevent_destroy)

# 7. (OPCIONAL) Destruir Bootstrap
cd ../../bootstrap
# CUIDADO: Isso deleta o estado de TODAS as stacks!
# terraform destroy -auto-approve
```

### 14.3 Limpeza de Recursos Orfaos

```bash
# Verificar Load Balancers orfaos
aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(LoadBalancerName, `elo-fraud`)].LoadBalancerArn'

# Verificar ENIs orfaos
aws ec2 describe-network-interfaces --filters "Name=description,Values=*elo-fraud*" --query 'NetworkInterfaces[*].[NetworkInterfaceId,Description]'

# Verificar Security Groups orfaos
aws ec2 describe-security-groups --filters "Name=tag:Name,Values=*elo-fraud*" --query 'SecurityGroups[*].[GroupId,GroupName]'
```

---

## 15. Checklist Final

### 15.1 Checklist de Deploy

- [ ] **Pre-requisitos**
  - [ ] Terraform >= 1.10.0 instalado
  - [ ] AWS CLI >= 2.15.0 instalado
  - [ ] kubectl >= 1.30.0 instalado
  - [ ] helm >= 3.14.0 instalado
  - [ ] docker >= 24.0.0 instalado
  - [ ] Credenciais AWS configuradas
  - [ ] Permissoes IAM suficientes

- [ ] **Bootstrap**
  - [ ] S3 bucket criado: `elo-fraud-terraform-state-888577064416-us-east-1`

- [ ] **Foundation**
  - [ ] VPC criada: `10.0.0.0/16`
  - [ ] 4 subnets criadas (2 publicas, 2 privadas)
  - [ ] NAT Gateway ativo
  - [ ] 11 VPC Endpoints criados
  - [ ] 7 S3 buckets criados

- [ ] **MLOps**
  - [ ] MLflow Tracking Server ativo
  - [ ] SageMaker Studio Domain criado
  - [ ] User Profile criado

- [ ] **Platform**
  - [ ] EKS Cluster ACTIVE
  - [ ] 2 nodes em estado Ready
  - [ ] ALB em estado active
  - [ ] NLB em estado active
  - [ ] API Gateway deployado
  - [ ] DynamoDB table criada
  - [ ] SQS FIFO + DLQ criadas
  - [ ] 5 ECR repositories criados (inference, process, model, best-model-register, etl-delta-filter)
  - [ ] 2 Firehose streams criados
  - [ ] Glue Database + Tables criados

- [ ] **Platform K8s**
  - [ ] Namespace `fraud-detection` criado
  - [ ] KEDA instalado e pods rodando
  - [ ] AWS Load Balancer Controller instalado
  - [ ] ConfigMaps criados (inference-config, process-config)
  - [ ] TargetGroupBinding criado

- [ ] **Platform Lambdas**
  - [ ] Lambda `register-best-model` criada
  - [ ] S3 trigger configurado

- [ ] **Servicos**
  - [ ] Imagem inference no ECR com tag `latest`
  - [ ] Imagem process no ECR com tag `latest`
  - [ ] Deployment inference com 2 replicas Running
  - [ ] Deployment process com 1 replica Running
  - [ ] Service inference respondendo na porta 8000
  - [ ] HPA inference configurado (2-6 replicas)
  - [ ] KEDA ScaledObject process configurado (1-5 replicas)
  - [ ] Pods registrados no ALB Target Group como healthy

- [ ] **Validacao E2E**
  - [ ] Health check via API Gateway retorna 200
  - [ ] POST /authorize-purchase retorna score
  - [ ] Mensagens chegam no SQS
  - [ ] Process consome mensagens
  - [ ] DynamoDB atualizado com transacoes
  - [ ] Dados chegam no S3 via Firehose

### 15.2 Metricas de Sucesso

| Metrica | Alvo | Como Verificar |
|---------|------|----------------|
| Health Check | 200 OK | `curl ${API_URL}/health` |
| Latencia p50 | < 200ms | CloudWatch API Gateway |
| Latencia p95 | < 500ms | CloudWatch API Gateway |
| Disponibilidade | > 99.9% | CloudWatch ALB |
| Error Rate | < 0.1% | CloudWatch API Gateway |
| SQS Age | < 60s | CloudWatch SQS |

### 15.3 Contatos

| Area | Responsavel |
|------|-------------|
| DevOps/Infra | Gustavo Liebl Pereira |
| ML/Data Science | Ana/Vinicios |
| Dados 3DS/TE40 | Denis |

---

## Apendice A: Arquivos de Referencia

### terraform.tfvars Completo (Foundation - DEV)

```hcl
# infra/environments/dev/foundation/terraform.tfvars
project_name   = "elo-fraud"
environment    = "dev"
aws_region     = "us-east-1"
aws_account_id = "888577064416"

vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

enable_nat_gateway         = true
single_nat_gateway         = true
enable_vpc_endpoints       = true
enable_interface_endpoints = true

s3_enable_versioning          = true
s3_force_destroy              = true
s3_raw_retention_days         = 30
s3_processed_retention_days   = 90
s3_logs_retention_days        = 90
s3_models_retention_enabled   = false
s3_enable_intelligent_tiering = true

common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Foundation"
  Region      = "us-east-1"
}
```

### Variaveis de Ambiente (Services)

> **NOTA**: Estas variaveis sao gerenciadas pelo Terraform via ConfigMaps.
> Arquivos: `infra/environments/dev/platform-k8s/configmaps.tf`

```bash
# Inference Service (ConfigMap: inference-config)
ENVIRONMENT=dev
LOG_LEVEL=INFO
AWS_REGION=us-east-1
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo
SQS_QUEUE_NAME=elo-fraud-resultset-dev.fifo
SQS_MESSAGE_GROUP_ID=inference-logs
MLFLOW_TRACKING_URI=<valor do output mlflow_tracking_uri da stack MLOps>
MODEL_NAME=Felicidade
USE_SQS=true
ENABLE_DEBUG=false

# Process Service (ConfigMap: process-config)
ENVIRONMENT=dev
LOG_LEVEL=INFO
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo
SQS_QUEUE_NAME=elo-fraud-resultset-dev.fifo
BATCH_SIZE=10
VISIBILITY_TIMEOUT=300
WAIT_TIME_SECONDS=20
MAX_EMPTY_RECEIVES=0
ENABLE_DYNAMODB=true
DYNAMODB_TABLE_NAME=elo-fraud-customer-recent-tx-dev
DYNAMO_TABLE=elo-fraud-customer-recent-tx-dev
ENABLE_S3=true
S3_BUCKET_NAME=elo-fraud-data-processed-dev-888577064416
S3_PREFIX=transaction-results
ENABLE_FIREHOSE=true
FIREHOSE_STREAM=<output firehose_delivery_stream_name da Platform>
FIREHOSE_INFERENCE_STREAM_NAME=<output firehose_inference_delivery_stream_name da Platform>
```

---

## Apendice B: Estimativa de Custos

| Servico | Quantidade | Custo Mensal (USD) |
|---------|------------|-------------------|
| VPC Interface Endpoints | 9 x 2 AZs | $129.60 |
| NAT Gateway | 1 | $32.00 + data |
| EKS Control Plane | 1 | $73.00 |
| EKS Nodes (t3.medium) | 2 | $60.00 |
| ALB | 1 | $16.00 + LCU |
| NLB | 1 | $18.00 + NLCU |
| API Gateway | ~100K requests | $3.50 |
| DynamoDB (On-Demand) | variavel | $5-20 |
| SQS | ~1M requests | $0.40 |
| Firehose | ~10GB/mes | $3.50 |
| S3 | ~50GB | $1.15 |
| ECR | ~5GB | $0.50 |
| CloudWatch | logs + metricas | $10.00 |
| MLflow Server (Small) | 1 | $50.00 |
| **TOTAL ESTIMADO** | | **$400-450/mes** |

---

*Documento gerado em 2026-02-01*
*Ultima atualizacao: 2026-02-05*
*Versao: 2.0.0*
