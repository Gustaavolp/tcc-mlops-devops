# Guia Completo: Criacao de Novo Ambiente

> **Autor**: Gustavo Liebl Pereira (DevOps)
> **Data**: 2026-01-19
> **Versao**: 1.0

Este documento descreve o passo a passo completo para criar um novo ambiente do projeto Elo Fraud Detection. O exemplo utiliza o ambiente **"teste"**, mas pode ser adaptado para qualquer nome de ambiente.

---

## Indice

1. [Visao Geral](#1-visao-geral)
2. [Pre-requisitos](#2-pre-requisitos)
3. [Passo 1: Criar Estrutura de Diretorios](#passo-1-criar-estrutura-de-diretorios)
4. [Passo 2: Foundation Stack](#passo-2-foundation-stack)
5. [Passo 3: MLOps Stack](#passo-3-mlops-stack)
6. [Passo 4: Platform Stack](#passo-4-platform-stack)
7. [Passo 5: Platform-K8s Stack](#passo-5-platform-k8s-stack)
8. [Passo 6: Manifests Kubernetes](#passo-6-manifests-kubernetes)
9. [Passo 7: Build e Push das Imagens Docker](#passo-7-build-e-push-das-imagens-docker)
10. [Passo 8: Validacao](#passo-8-validacao)
11. [Checklist Resumido](#checklist-resumido)
12. [Estimativa de Custos](#estimativa-de-custos)
13. [Destruicao do Ambiente](#destruicao-do-ambiente)

---

## 1. Visao Geral

### 1.1 Estrutura de Stacks

O ambiente e composto por **4 stacks Terraform** + **manifests Kubernetes**:

```
Ordem de Deploy:
┌─────────────────┐
│   1. FOUNDATION  │ VPC + S3 Buckets
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌─────────┐
│2. MLOPS│  │3.PLATFORM│ (podem ser paralelos)
└────────┘  └────┬────┘
                 │
                 ▼
         ┌──────────────┐
         │4. PLATFORM-K8S│ ConfigMaps, Helm, TargetGroupBinding
         └──────────────┘
                 │
                 ▼
         ┌──────────────┐
         │5. K8S MANIFESTS│ Deployments, Services, HPA
         └──────────────┘
```

### 1.2 Recursos Criados por Stack

| Stack | Recursos |
|-------|----------|
| **Foundation** | VPC, Subnets, NAT Gateway, VPC Endpoints, 7 S3 Buckets |
| **MLOps** | MLflow Tracking Server, SageMaker Studio Domain |
| **Platform** | EKS, ALB, API Gateway, DynamoDB, SQS, ECR, Firehose, Athena, Lambda |
| **Platform-K8s** | ConfigMaps, TargetGroupBinding, Helm releases |
| **K8s Manifests** | Namespace, ServiceAccounts, Deployments, Services, HPA |

### 1.3 Configuracoes para o Ambiente "teste"

| Configuracao | Valor | Justificativa |
|--------------|-------|---------------|
| **Regiao** | `us-east-2` | Regiao diferente para isolamento |
| **VPC CIDR** | `10.2.0.0/16` | Nao conflita com dev (10.0) e staging (10.1) |
| **Environment** | `teste` | Nome do ambiente |
| **Suffix** | `-teste` | Sufixo para recursos |
| **State Bucket** | `us-east-1` | Bucket de state compartilhado (ja existente) |

> **NOTA**: O bucket de state do Terraform permanece em `us-east-1` pois e um recurso compartilhado ja existente. Apenas os recursos do ambiente serao criados em `us-east-2`.

---

## 2. Pre-requisitos

### 2.1 Ferramentas Necessarias

```bash
# Terraform >= 1.10.0 (recomendado: 1.11.0)
terraform --version

# AWS CLI >= 2.0
aws --version

# kubectl >= 1.28
kubectl version --client

# Docker >= 24.0
docker --version

# Helm >= 3.0
helm version
```

### 2.2 Credenciais AWS

```bash
# Configurar credenciais
aws configure --profile elo

# Ou usar SSO
aws sso login --profile elo

# Verificar identidade
aws sts get-caller-identity --profile elo
```

### 2.3 Variaveis de Ambiente

```bash
export AWS_PROFILE=elo
export AWS_REGION=us-east-2
export AWS_ACCOUNT_ID=888577064416
export ENVIRONMENT=teste
```

---

## Passo 1: Criar Estrutura de Diretorios

```bash
# Diretorios Terraform
mkdir -p infra/environments/teste/foundation
mkdir -p infra/environments/teste/mlops
mkdir -p infra/environments/teste/platform
mkdir -p infra/environments/teste/platform-k8s

# Diretorios K8s
mkdir -p k8s/teste/inference
mkdir -p k8s/teste/process

# Verificar estrutura
tree infra/environments/teste/
tree k8s/teste/
```

---

## Passo 2: Foundation Stack

A Foundation Stack cria a base de infraestrutura: VPC e S3 Buckets.

### 2.1 Copiar todos os arquivos do ambiente dev

```bash
cd infra/environments/teste/foundation

# Copiar TODOS os arquivos de dev como base
cp ../../dev/foundation/*.tf .
```

### 2.2 Editar `backend.tf`

Alterar apenas a **key** do state:

```bash
# Editar backend.tf
# Alterar: key = "dev/foundation/terraform.tfstate"
# Para:    key = "teste/foundation/terraform.tfstate"
```

```hcl
# infra/environments/teste/foundation/backend.tf

terraform {
  backend "s3" {
    bucket         = "elo-fraud-terraform-state-888577064416-us-east-1"
    key            = "teste/foundation/terraform.tfstate"  # <-- ALTERAR AQUI
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "elo-fraud-terraform-state-lock"
  }
}
```

### 2.3 Editar `variables.tf`

Copiar de dev e alterar **apenas** as variaveis necessarias:

**Alteracoes necessarias no `variables.tf`:**

| Variavel | Valor Original (dev) | Novo Valor (teste) |
|----------|---------------------|-------------------|
| `environment` | `"dev"` | `"teste"` |
| `aws_region` | `"us-east-1"` | `"us-east-2"` |
| `availability_zones` | `["us-east-1a", "us-east-1b"]` | `["us-east-2a", "us-east-2b"]` |
| `vpc_cidr` | `"10.0.0.0/16"` | `"10.2.0.0/16"` |
| `public_subnet_cidrs` | `["10.0.1.0/24", "10.0.2.0/24"]` | `["10.2.1.0/24", "10.2.2.0/24"]` |
| `private_subnet_cidrs` | `["10.0.11.0/24", "10.0.12.0/24"]` | `["10.2.11.0/24", "10.2.12.0/24"]` |
| `common_tags.Environment` | `"dev"` | `"teste"` |
| `common_tags.Region` | `"us-east-1"` | `"us-east-2"` |

> **IMPORTANTE**: Mantenha todas as outras variaveis inalteradas para garantir consistencia com o ambiente de referencia.

### 2.4 Executar Foundation

```bash
cd infra/environments/teste/foundation

# Inicializar
terraform init

# Planejar
terraform plan -out=tfplan

# Aplicar
terraform apply tfplan

# Verificar outputs
terraform output
```

### 2.5 Outputs Esperados

```
vpc_id = "vpc-xxxxxxxxxxxxxxxxx"
vpc_cidr = "10.2.0.0/16"
public_subnet_ids = ["subnet-xxx", "subnet-xxx"]
private_subnet_ids = ["subnet-xxx", "subnet-xxx"]
s3_raw_bucket_id = "elo-fraud-data-raw-teste-888577064416"
s3_processed_bucket_id = "elo-fraud-data-processed-teste-888577064416"
```

---

## Passo 3: MLOps Stack

A MLOps Stack cria o MLflow Tracking Server e SageMaker Studio.

### 3.1 Copiar todos os arquivos do ambiente dev

```bash
cd infra/environments/teste/mlops

# Copiar TODOS os arquivos de dev como base
cp ../../dev/mlops/*.tf .
```

### 3.2 Editar `backend.tf`

Alterar apenas a **key** do state:

```bash
# Editar backend.tf
# Alterar: key = "dev/mlops/terraform.tfstate"
# Para:    key = "teste/mlops/terraform.tfstate"
```

```hcl
# infra/environments/teste/mlops/backend.tf

terraform {
  backend "s3" {
    bucket         = "elo-fraud-terraform-state-888577064416-us-east-1"
    key            = "teste/mlops/terraform.tfstate"  # <-- ALTERAR AQUI
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "elo-fraud-terraform-state-lock"
  }
}
```

### 3.3 Editar `data.tf`

Alterar apenas a **key** do remote state da Foundation:

```bash
# Editar data.tf
# Alterar: key = "dev/foundation/terraform.tfstate"
# Para:    key = "teste/foundation/terraform.tfstate"
```

### 3.4 Editar `variables.tf`

Copiar de dev e alterar **apenas** as variaveis necessarias:

**Alteracoes necessarias no `variables.tf`:**

| Variavel | Valor Original (dev) | Novo Valor (teste) |
|----------|---------------------|-------------------|
| `environment` | `"dev"` | `"teste"` |
| `aws_region` | `"us-east-1"` | `"us-east-2"` |
| `mlflow_environment` | `"dev"` | `"tst"` |
| `common_tags.Environment` | `"dev"` | `"teste"` |
| `common_tags.Region` | `"us-east-1"` | `"us-east-2"` |

> **IMPORTANTE**: Mantenha todas as outras variaveis inalteradas para garantir consistencia com o ambiente de referencia.

### 3.5 Executar MLOps

```bash
cd infra/environments/teste/mlops

terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output
```

---

## Passo 4: Platform Stack

A Platform Stack cria os recursos principais: EKS, ALB, API Gateway, DynamoDB, SQS, etc.

### 4.1 Copiar todos os arquivos do ambiente dev

```bash
cd infra/environments/teste/platform

# Copiar TODOS os arquivos de dev como base
cp ../../dev/platform/*.tf .
```

### 4.2 Editar `backend.tf`

Alterar apenas a **key** do state:

```bash
# Editar backend.tf
# Alterar: key = "dev/platform/terraform.tfstate"
# Para:    key = "teste/platform/terraform.tfstate"
```

```hcl
# infra/environments/teste/platform/backend.tf

terraform {
  backend "s3" {
    bucket         = "elo-fraud-terraform-state-888577064416-us-east-1"
    key            = "teste/platform/terraform.tfstate"  # <-- ALTERAR AQUI
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "elo-fraud-terraform-state-lock"
  }
}
```

### 4.3 Editar `data.tf`

Alterar as **keys** dos remote states (Foundation e MLOps):

```bash
# Editar data.tf
# Alterar: key = "dev/foundation/terraform.tfstate"
# Para:    key = "teste/foundation/terraform.tfstate"
#
# Alterar: key = "dev/mlops/terraform.tfstate"
# Para:    key = "teste/mlops/terraform.tfstate"
```

### 4.4 Editar `variables.tf`

Copiar de dev e alterar **apenas** as variaveis necessarias:

**Alteracoes necessarias no `variables.tf`:**

| Variavel | Valor Original (dev) | Novo Valor (teste) |
|----------|---------------------|-------------------|
| `environment` | `"dev"` | `"teste"` |
| `aws_region` | `"us-east-1"` | `"us-east-2"` |
| `vpc_cidr` | `"10.0.0.0/16"` | `"10.2.0.0/16"` |
| `availability_zones` | `["us-east-1a", "us-east-1b"]` | `["us-east-2a", "us-east-2b"]` |
| `common_tags.Environment` | `"dev"` | `"teste"` |
| `common_tags.Region` | `"us-east-1"` | `"us-east-2"` |

> **IMPORTANTE**: Mantenha todas as outras variaveis inalteradas (EKS, GitHub OIDC, etc.) para garantir consistencia com o ambiente de referencia.

### 4.5 Executar Platform

```bash
cd infra/environments/teste/platform

terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output
```

---

## Passo 5: Platform-K8s Stack

A Platform-K8s Stack cria recursos Kubernetes via Terraform: ConfigMaps, TargetGroupBinding, Helm.

### 5.1 Copiar todos os arquivos do ambiente dev

```bash
cd infra/environments/teste/platform-k8s

# Copiar TODOS os arquivos de dev como base
cp ../../dev/platform-k8s/*.tf .
```

### 5.2 Editar `backend.tf`

Alterar apenas a **key** do state:

```bash
# Editar backend.tf
# Alterar: key = "dev/platform-k8s/terraform.tfstate"
# Para:    key = "teste/platform-k8s/terraform.tfstate"
```

```hcl
# infra/environments/teste/platform-k8s/backend.tf

terraform {
  backend "s3" {
    bucket         = "elo-fraud-terraform-state-888577064416-us-east-1"
    key            = "teste/platform-k8s/terraform.tfstate"  # <-- ALTERAR AQUI
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "elo-fraud-terraform-state-lock"
  }
}
```

### 5.3 Editar `data.tf`

Alterar as **keys** dos remote states (Platform e MLOps):

```bash
# Editar data.tf
# Alterar: key = "dev/platform/terraform.tfstate"
# Para:    key = "teste/platform/terraform.tfstate"
#
# Alterar: key = "dev/mlops/terraform.tfstate"
# Para:    key = "teste/mlops/terraform.tfstate"
```

### 5.4 Editar `variables.tf`

Copiar de dev e alterar **apenas** as variaveis necessarias:

**Alteracoes necessarias no `variables.tf`:**

| Variavel | Valor Original (dev) | Novo Valor (teste) |
|----------|---------------------|-------------------|
| `environment` | `"dev"` | `"teste"` |
| `aws_region` | `"us-east-1"` | `"us-east-2"` |
| `common_tags.Environment` | `"dev"` | `"teste"` |
| `common_tags.Region` | `"us-east-1"` | `"us-east-2"` |

> **IMPORTANTE**: Mantenha todas as outras variaveis inalteradas para garantir consistencia com o ambiente de referencia.

### 5.5 Executar Platform-K8s

```bash
cd infra/environments/teste/platform-k8s

terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output
```

---

## Passo 6: Manifests Kubernetes

### 6.1 Configurar kubectl

```bash
aws eks update-kubeconfig --name elo-fraud-cluster-teste --region us-east-2

# Verificar conexao
kubectl cluster-info
kubectl get nodes
```

### 6.2 Copiar todos os arquivos do ambiente staging

O ambiente staging possui os manifests mais completos. Copiar como base:

```bash
# Copiar estrutura completa de staging
cp -r k8s/staging/* k8s/teste/

# Verificar estrutura
tree k8s/teste/
```

Estrutura esperada:
```
k8s/teste/
├── namespace.yaml
├── serviceaccount-inference.yaml
├── serviceaccount-process.yaml
├── inference/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
└── process/
    ├── deployment.yaml
    └── hpa.yaml
```

### 6.3 Editar os arquivos - Alteracoes necessarias

Usar `sed` para substituir valores em massa ou editar manualmente:

```bash
cd k8s/teste

# Substituir 'staging' por 'teste' em todos os arquivos
find . -name "*.yaml" -exec sed -i 's/staging/teste/g' {} \;

# Substituir imagens ECR (de staging para teste)
find . -name "*.yaml" -exec sed -i 's/elo-fraud-inference-staging/elo-fraud-inference-teste/g' {} \;
find . -name "*.yaml" -exec sed -i 's/elo-fraud-process-staging/elo-fraud-process-teste/g' {} \;

# Substituir regiao ECR (de us-east-1 para us-east-2)
find . -name "*.yaml" -exec sed -i 's/us-east-1/us-east-2/g' {} \;
```

**Alteracoes por arquivo:**

| Arquivo | Campo | Valor Original (staging) | Novo Valor (teste) |
|---------|-------|-------------------------|-------------------|
| `namespace.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `namespace.yaml` | `metadata.annotations.description` | `...Staging` | `...Teste` |
| `serviceaccount-*.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `inference/deployment.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `inference/deployment.yaml` | `spec.template.spec.containers[0].image` | `...-staging:latest` | `...-teste:latest` |
| `inference/service.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `inference/hpa.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `process/deployment.yaml` | `metadata.labels.environment` | `staging` | `teste` |
| `process/deployment.yaml` | `spec.template.spec.containers[0].image` | `...-staging:latest` | `...-teste:latest` |
| `process/hpa.yaml` | `metadata.labels.environment` | `staging` | `teste` |

> **NOTA**: Os ConfigMaps (`inference-config` e `process-config`) sao gerenciados pelo Terraform na stack Platform-K8s, nao precisam ser criados manualmente.

### 6.4 Aplicar Manifests K8s

```bash
# Ordem de aplicacao
kubectl apply -f k8s/teste/namespace.yaml
kubectl apply -f k8s/teste/serviceaccount-inference.yaml
kubectl apply -f k8s/teste/serviceaccount-process.yaml
kubectl apply -f k8s/teste/inference/
kubectl apply -f k8s/teste/process/

# Verificar
kubectl get all -n fraud-detection
```

---

## Passo 7: Build e Push das Imagens Docker

### 7.1 Repositorios ECR

Os repositorios sao criados automaticamente pelo Terraform (Platform Stack):

- `elo-fraud-inference-teste`
- `elo-fraud-process-teste`
- `elo-fraud-model-teste`

### 7.2 Login no ECR

```bash
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-2.amazonaws.com
```

### 7.3 Build e Push - Inference

```bash
# Build
docker build -t elo-fraud-inference-teste:latest ./services/inference

# Tag
docker tag elo-fraud-inference-teste:latest \
  888577064416.dkr.ecr.us-east-2.amazonaws.com/elo-fraud-inference-teste:latest

# Push
docker push 888577064416.dkr.ecr.us-east-2.amazonaws.com/elo-fraud-inference-teste:latest
```

### 7.4 Build e Push - Process

```bash
# Build
docker build -t elo-fraud-process-teste:latest ./services/process

# Tag
docker tag elo-fraud-process-teste:latest \
  888577064416.dkr.ecr.us-east-2.amazonaws.com/elo-fraud-process-teste:latest

# Push
docker push 888577064416.dkr.ecr.us-east-2.amazonaws.com/elo-fraud-process-teste:latest
```

### 7.5 Usar Pipeline GitHub Actions (Alternativa)

Execute o workflow `docker-ecr.yml` manualmente:

1. Va para GitHub Actions
2. Selecione "Docker Build & Push to ECR"
3. Clique em "Run workflow"
4. Preencha os parametros:
   - Branch: `gustaavolp-compasso`
   - Target Environment: `dev` (ou crie uma opcao para teste)
   - Credenciais AWS temporarias

---

## Passo 8: Validacao

### 8.1 Verificar recursos Terraform

```bash
# Foundation
cd infra/environments/teste/foundation
terraform output

# MLOps
cd ../mlops
terraform output

# Platform
cd ../platform
terraform output

# Platform-K8s
cd ../platform-k8s
terraform output
```

### 8.2 Verificar Kubernetes

```bash
# Namespace
kubectl get namespace fraud-detection

# Pods
kubectl get pods -n fraud-detection

# Services
kubectl get svc -n fraud-detection

# HPA
kubectl get hpa -n fraud-detection

# ConfigMaps (criados pelo Terraform)
kubectl get configmaps -n fraud-detection

# Descrever pods
kubectl describe pods -n fraud-detection

# Logs
kubectl logs -f deployment/inference -n fraud-detection
kubectl logs -f deployment/process -n fraud-detection
```

### 8.3 Testar Endpoints

```bash
# Obter ALB DNS
ALB_DNS=$(terraform -chdir=infra/environments/teste/platform output -raw alb_dns_name)

# Health check direto no ALB
curl http://${ALB_DNS}/health

# Obter URL do API Gateway
API_URL=$(terraform -chdir=infra/environments/teste/platform output -raw api_gateway_invoke_url)

# Health check via API Gateway
curl ${API_URL}/health

# Score endpoint
curl -X POST ${API_URL}/v1/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test-123",
    "amount": 100.00,
    "cardHolderDocument": "12345678900",
    "merchantCategory": "5411"
  }'
```

### 8.4 Verificar SQS

```bash
# Obter URL da fila
SQS_URL=$(terraform -chdir=infra/environments/teste/platform output -raw sqs_queue_url)

# Enviar mensagem de teste
aws sqs send-message \
  --queue-url ${SQS_URL} \
  --message-body '{"transaction_id": "test-123", "fraud_label": 0}' \
  --message-group-id "test-group" \
  --region us-east-2

# Verificar metricas da fila
aws sqs get-queue-attributes \
  --queue-url ${SQS_URL} \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-2
```

---

## Checklist Resumido

| # | Etapa | Comando | Status |
|---|-------|---------|--------|
| 1 | Criar diretorios Terraform | `mkdir -p infra/environments/teste/{foundation,mlops,platform,platform-k8s}` | ⬜ |
| 2 | Criar diretorios K8s | `mkdir -p k8s/teste/{inference,process}` | ⬜ |
| 3 | Foundation - copiar/criar arquivos | Copiar .tf + criar variables.tf, backend.tf | ⬜ |
| 4 | Foundation - terraform apply | `terraform init && terraform apply` | ⬜ |
| 5 | MLOps - copiar/criar arquivos | Copiar .tf + criar variables.tf, backend.tf, data.tf | ⬜ |
| 6 | MLOps - terraform apply | `terraform init && terraform apply` | ⬜ |
| 7 | Platform - copiar/criar arquivos | Copiar .tf + criar variables.tf, backend.tf, data.tf | ⬜ |
| 8 | Platform - terraform apply | `terraform init && terraform apply` | ⬜ |
| 9 | Platform-K8s - copiar/criar arquivos | Copiar .tf + criar variables.tf, backend.tf, data.tf | ⬜ |
| 10 | Platform-K8s - terraform apply | `terraform init && terraform apply` | ⬜ |
| 11 | Configurar kubectl | `aws eks update-kubeconfig --name elo-fraud-cluster-teste --region us-east-2` | ⬜ |
| 12 | Criar manifests K8s | Criar arquivos YAML | ⬜ |
| 13 | Aplicar manifests K8s | `kubectl apply -f k8s/teste/` | ⬜ |
| 14 | Build imagens Docker | `docker build && docker push` | ⬜ |
| 15 | Validar deployment | `kubectl get pods -n fraud-detection` | ⬜ |
| 16 | Testar endpoints | `curl ${API_URL}/health` | ⬜ |

---

## Estimativa de Custos

### Custo Mensal Estimado (Ambiente Teste)

| Servico | Configuracao | Custo/mes |
|---------|-------------|-----------|
| EKS Control Plane | 1 cluster | ~$73 |
| EC2 (t3.medium) | 1 node | ~$30 |
| NAT Gateway | 1 gateway (single) | ~$32 |
| ALB | 1 load balancer | ~$18 |
| DynamoDB | PAY_PER_REQUEST | ~$5 |
| SQS FIFO | ~1M msgs | ~$2 |
| S3 | ~100GB | ~$5 |
| Firehose | 2 streams | ~$2 |
| MLflow (Small) | SageMaker Managed | ~$0 |
| ECR | 3 repos | ~$2 |
| CloudWatch | Logs + Metrics | ~$5 |
| API Gateway | ~1M requests | ~$4 |
| **TOTAL** | | **~$178-200/mes** |

### Otimizacoes de Custo

- NAT Gateway single (nao HA)
- t3.medium nodes (2 vCPU, 4GB)
- DynamoDB on-demand (sem provisioned capacity)
- MLflow Small (pode aumentar se necessario)
- Lifecycle policies no S3 (Glacier apos 30-90 dias)

---

## Destruicao do Ambiente

**IMPORTANTE**: Destruir na ordem **INVERSA** da criacao!

### Ordem de Destruicao

```bash
# 1. Deletar manifests K8s
kubectl delete -f k8s/teste/process/
kubectl delete -f k8s/teste/inference/
kubectl delete -f k8s/teste/serviceaccount-process.yaml
kubectl delete -f k8s/teste/serviceaccount-inference.yaml
kubectl delete -f k8s/teste/namespace.yaml

# 2. Destruir Platform-K8s
cd infra/environments/teste/platform-k8s
terraform destroy -auto-approve

# 3. Destruir Platform
cd ../platform
terraform destroy -auto-approve

# 4. Destruir MLOps
cd ../mlops
terraform destroy -auto-approve

# 5. Destruir Foundation
cd ../foundation
terraform destroy -auto-approve

# 6. (Opcional) Remover diretorios
rm -rf infra/environments/teste/
rm -rf k8s/teste/
```

### Notas sobre Destruicao

- O `s3_force_destroy = true` permite deletar buckets com objetos
- DynamoDB sera deletado (dados perdidos)
- ECR repositories serao deletados (imagens perdidas)
- EKS cluster sera completamente removido

---

## Referencias

| Documento | Caminho |
|-----------|---------|
| Claude.md (contexto geral) | `Claude.md` |
| Arquitetura do Projeto | `docs/ARCHITECTURE_OVERVIEW.md` |
| Modulos Terraform | `infra/modules/` |
| Ambiente DEV (referencia) | `infra/environments/dev/` |
| Ambiente STAGING (referencia) | `infra/environments/staging/` |
| K8s DEV (referencia) | `k8s/dev/` |
| K8s STAGING (referencia) | `k8s/staging/` |

---

*Documento criado em 2026-01-19 por Claude Code assistindo Gustavo Liebl Pereira.*
