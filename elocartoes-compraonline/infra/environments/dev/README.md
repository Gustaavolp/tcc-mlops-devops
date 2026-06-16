# Ambiente DEV - Elo Fraud Detection

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Stacks](#stacks)
- [Configuracoes do Ambiente](#configuracoes-do-ambiente)
- [Ordem de Implantacao](#ordem-de-implantacao)
- [Guia de Implantacao Completa](#guia-de-implantacao-completa)
- [Custos Estimados](#custos-estimados)
- [Diferencas para Outros Ambientes](#diferencas-para-outros-ambientes)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

O ambiente **DEV** e o ambiente de desenvolvimento do sistema de deteccao de fraude Elo. Configurado para **otimizar custos** e **agilidade de desenvolvimento**, com trade-offs aceitaveis em alta disponibilidade e seguranca avancada.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Desenvolvimento** | Ambiente para desenvolvedores testarem mudancas |
| **Integracao** | Validar integracao entre componentes antes de staging |
| **Experimentacao** | Data Scientists podem experimentar modelos ML |
| **CI/CD** | Pipeline de deploy automatizado para validacao |

### Caracteristicas Principais

| Caracteristica | Valor | Justificativa |
|----------------|-------|---------------|
| **Regiao** | us-east-1 | Menor custo, mais servicos disponiveis |
| **Alta Disponibilidade** | Minima (2 AZs) | Custo reduzido, redundancia basica |
| **Seguranca** | Basica | HTTP (sem TLS), sem WAF |
| **Escalabilidade** | Limitada | 1-3 nodes EKS, recursos minimos |
| **Retencao de Dados** | Reduzida | Logs 14-90 dias, Glacier apos 30-90 dias |

---

## Arquitetura

```
                              AWS Region: us-east-1
                              Account: 888577064416
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              VPC: 10.0.0.0/16                                   │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        Availability Zone: us-east-1a                     │  │
│   │                                                                          │  │
│   │   Public Subnet                    Private Subnet                        │  │
│   │   10.0.1.0/24                      10.0.11.0/24                          │  │
│   │   ┌─────────────┐                  ┌─────────────────────────────────┐  │  │
│   │   │             │                  │  EKS Node                       │  │  │
│   │   │   (vazio)   │                  │  ┌───────────┐  ┌───────────┐  │  │  │
│   │   │             │                  │  │ Inference │  │  Process  │  │  │  │
│   │   └─────────────┘                  │  │   Pod     │  │   Pod     │  │  │  │
│   │                                    │  └───────────┘  └───────────┘  │  │  │
│   │                                    └─────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        Availability Zone: us-east-1b                     │  │
│   │                                                                          │  │
│   │   Public Subnet                    Private Subnet                        │  │
│   │   10.0.2.0/24                      10.0.12.0/24                          │  │
│   │   ┌─────────────┐                  ┌─────────────────────────────────┐  │  │
│   │   │             │                  │  (disponivel para scaling)      │  │  │
│   │   │   (vazio)   │                  │                                 │  │  │
│   │   │             │                  │                                 │  │  │
│   │   └─────────────┘                  └─────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                           VPC Endpoints (11)                             │  │
│   │                                                                          │  │
│   │   S3 (Gateway) │ DynamoDB (Gateway) │ ECR API │ ECR DKR │ CloudWatch    │  │
│   │   SQS │ STS │ EC2 │ SageMaker API │ SageMaker Runtime │ Firehose       │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        │ Internet
                                        ▼

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway (Regional)                             │
│                                                                                 │
│   POST /v1/authorize-purchase ─▶ VPC Link ─▶ NLB ─▶ ALB ─▶ Inference Pod      │
│   GET /health ────────────────▶ VPC Link ─▶ NLB ─▶ ALB ─▶ Inference Pod       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
AUTHORIZE-PURCHASE (Sincrono - p95 < 500ms):
────────────────────────────────────────────────────────────────────────

   Cliente ──▶ API Gateway ──▶ VPC Link ──▶ NLB ──▶ ALB ──▶ Inference Pod
                                                              │
                                                              ├──▶ DynamoDB (features)
                                                              │
                                                              └──▶ Response (score + recommendation)


FEEDBACK (Assincrono):
────────────────────────────────────────────────────────────────────────

   Elo Backend ──▶ SQS FIFO ──▶ Process Pod ──┬──▶ DynamoDB (update)
                                              │
                                              ├──▶ Firehose ──▶ S3 landing_zone/
                                              │
                                              └──▶ Firehose ──▶ S3 inference_logs/


ML TRAINING (Batch):
────────────────────────────────────────────────────────────────────────

   S3 landing_zone/ ──▶ Glue ETL ──▶ S3 transformed_zone/
                                              │
                                              ▼
   SageMaker Studio ◀──────────────── Athena Queries
         │
         ▼
   MLflow Model Registry ◀──── Lambda (register-best-model)
```

---

## Stacks

O ambiente DEV e composto por **5 stacks Terraform** independentes, cada uma com seu proprio state file:

### Resumo das Stacks

| Stack | Descricao | State Key |
|-------|-----------|-----------|
| **[foundation](./foundation/)** | VPC, Subnets, S3 Buckets, VPC Endpoints | `dev/foundation/terraform.tfstate` |
| **[mlops](./mlops/)** | MLflow, SageMaker Studio | `dev/mlops/terraform.tfstate` |
| **[platform](./platform/)** | EKS, ALB, NLB, API Gateway, DynamoDB, SQS, ECR, Firehose, Athena, Glue | `dev/platform/terraform.tfstate` |
| **[platform-k8s](./platform-k8s/)** | Helm charts, ConfigMaps, HPA, KEDA, PDBs, TargetGroupBinding | `dev/platform-k8s/terraform.tfstate` |
| **[platform-lambdas](./platform-lambdas/)** | Lambda register-best-model (container) | `dev/platform-lambdas/terraform.tfstate` |

### Foundation

Infraestrutura base consumida por todas as outras stacks via `terraform_remote_state`.

| Recurso | Configuracao DEV |
|---------|------------------|
| **VPC** | 10.0.0.0/16, 2 AZs (us-east-1a, us-east-1b) |
| **Subnets Publicas** | 10.0.1.0/24, 10.0.2.0/24 |
| **Subnets Privadas** | 10.0.11.0/24, 10.0.12.0/24 |
| **NAT Gateway** | Desabilitado (usa VPC Endpoints) |
| **VPC Endpoints** | 11 endpoints (S3, DynamoDB, ECR, SQS, Firehose, etc.) |
| **S3 raw** | Intelligent Tiering, 30d → Glacier |
| **S3 processed** | Bronze/Silver/Gold, 90d → Glacier |
| **S3 models** | Versionado, sem expiracao |
| **S3 logs** | 90 dias expiracao |
| **S3 resources** | Recursos estaticos (templates, configs) |
| **S3 reports_promotion** | Relatorios de promocao |
| **S3 reports_statistics** | Relatorios estatisticos |

### MLOps

Ferramentas para o time de Data Science.

| Recurso | Configuracao DEV |
|---------|------------------|
| **MLflow Tracking Server** | Small size, v3.0 |
| **MLflow Artifacts** | S3, retencao 90 dias |
| **MLflow Logs** | 7 dias retencao |
| **SageMaker Studio** | ml.t3.medium, shutdown 60min |
| **SageMaker Studio Acesso** | Publico (sem VPC only) |

### Platform

Stack principal da aplicacao de deteccao de fraude.

| Recurso | Configuracao DEV |
|---------|------------------|
| **EKS Cluster** | v1.32, endpoint publico+privado |
| **EKS Nodes** | t3.medium, min 1 / max 3 |
| **ALB** | Interno, HTTP:80, /health check |
| **NLB** | Interno, TCP:80 (VPC Link) |
| **API Gateway** | REST Regional, VPC Link, 5000 burst / 10000 rate |
| **DynamoDB** | PAY_PER_REQUEST |
| **SQS** | FIFO, 5min visibility, 14d retencao, DLQ 3 tentativas |
| **ECR** | 3 repos, scan on push, 30 imagens max |
| **Firehose** | 2 streams, 1MB buffer, 60s interval |
| **Athena** | 10GB/query limit |
| **Glue** | 2 jobs ETL, schedule semanal |

### Platform-K8s

Recursos Kubernetes gerenciados pelo Terraform.

| Recurso | Configuracao DEV |
|---------|------------------|
| **Metrics Server** | v3.12.0, 1 replica |
| **Cluster Autoscaler** | v9.37.0, 1 replica |
| **AWS LB Controller** | v1.17.1, 2 replicas |
| **KEDA** | v2.17.3, 1 replica operator |
| **HPA Inference** | min 2 / max 6, CPU 50% |
| **ScaledObject Process** | min 1 / max 5, SQS trigger |
| **PDBs** | minAvailable 1 para inference e process |
| **ConfigMaps** | inference-config, process-config |

### Platform-Lambdas

Lambda functions container-based.

| Recurso | Configuracao DEV |
|---------|------------------|
| **register-best-model** | Container, 512MB, 300s timeout |
| **Trigger** | S3 ObjectCreated no bucket SageMaker |
| **Funcao** | Registra melhor modelo no MLflow |

---

## Configuracoes do Ambiente

### Rede

| Configuracao | Valor | Observacao |
|--------------|-------|------------|
| VPC CIDR | 10.0.0.0/16 | |
| Availability Zones | 2 | us-east-1a, us-east-1b |
| NAT Gateway | Desabilitado | VPC Endpoints substituem |
| VPC Endpoints | 11 | Acesso privado a servicos AWS |
| Internet Gateway | Habilitado | Para subnets publicas |

### Armazenamento

| Configuracao | Valor | Observacao |
|--------------|-------|------------|
| S3 Versioning | Habilitado | Todos os buckets |
| S3 force_destroy | Habilitado | Permite deletar buckets com conteudo |
| Intelligent Tiering | Habilitado | Otimizacao automatica de custo |
| Raw → Glacier | 30 dias | |
| Processed → Glacier | 90 dias | |
| Logs expiration | 90 dias | |
| Models expiration | Desabilitado | Versionamento mantem historico |

### Compute

| Configuracao | Valor | Observacao |
|--------------|-------|------------|
| EKS Version | 1.32 | |
| Node Type | t3.medium | 2 vCPU, 4GB RAM |
| Node Count | 1 (min 1, max 3) | Escala sob demanda |
| Studio Idle Shutdown | 60 minutos | Economia de custo |

### Seguranca e Protecao

| Configuracao | Valor | Observacao |
|--------------|-------|------------|
| HTTPS/TLS | Desabilitado | HTTP direto no ALB |
| WAF | Desabilitado | Sem protecao de borda |
| ALB Deletion Protection | Desabilitado | Facilita cleanup |
| DynamoDB Streams | Desabilitado | |
| ECR Tag Mutability | MUTABLE | Permite sobrescrever tags |
| KMS | AWS Managed Keys | Sem CMK customizada |

---

## Ordem de Implantacao

As stacks devem ser aplicadas na seguinte ordem devido a dependencias via `terraform_remote_state`:

```
1. bootstrap (centralizado - ja aplicado)
       │
       ▼
2. foundation
       │
       ├─────────────────────┐
       ▼                     ▼
3. mlops               platform
                             │
                             ▼
                       platform-k8s
                             │
                             ▼
                       platform-lambdas
```

### Diagrama de Dependencias Detalhado

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   BOOTSTRAP (us-east-1)                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  S3 Bucket: elo-fraud-terraform-state-888577064416-us-east-1        │   │
│   │  - Armazena todos os state files                                     │   │
│   │  - use_lockfile = true (S3 native locking)                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  FOUNDATION                                                          │   │
│   │                                                                      │   │
│   │  Outputs:                                                            │   │
│   │  - vpc_id                    - public_subnet_ids                     │   │
│   │  - vpc_cidr                  - private_subnet_ids                    │   │
│   │  - s3_raw_bucket_arn         - s3_processed_bucket_arn               │   │
│   │  - s3_models_bucket_arn      - s3_logs_bucket_arn                    │   │
│   │  - security_group_alb_id                                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                    │                              │                          │
│                    ▼                              ▼                          │
│   ┌────────────────────────────┐    ┌────────────────────────────────────┐  │
│   │  MLOPS                     │    │  PLATFORM                          │  │
│   │                            │    │                                    │  │
│   │  Consome:                  │    │  Consome:                          │  │
│   │  - vpc_id                  │    │  - vpc_id, vpc_cidr                │  │
│   │  - private_subnet_ids      │    │  - private_subnet_ids              │  │
│   │  - s3_models_bucket_arn    │    │  - s3_* bucket ARNs                │  │
│   │                            │    │  - security_group_alb_id           │  │
│   │  Outputs:                  │    │                                    │  │
│   │  - mlflow_tracking_uri     │    │  Outputs:                          │  │
│   │                            │    │  - eks_cluster_name/endpoint       │  │
│   └────────────────────────────┘    │  - target_group_arn                │  │
│                                     │  - dynamodb_table_name             │  │
│                                     │  - sqs_queue_url                   │  │
│                                     │  - ecr_*_repository_url            │  │
│                                     │  - firehose_*_stream_name          │  │
│                                     └─────────────────┬──────────────────┘  │
│                                                       │                      │
│                                                       ▼                      │
│                                     ┌────────────────────────────────────┐  │
│                                     │  PLATFORM-K8S                      │  │
│                                     │                                    │  │
│                                     │  Consome:                          │  │
│                                     │  - eks_cluster_name/endpoint       │  │
│                                     │  - target_group_arn                │  │
│                                     │  - dynamodb_table_name             │  │
│                                     │  - sqs_queue_url                   │  │
│                                     │  - firehose_*_stream_name          │  │
│                                     └─────────────────┬──────────────────┘  │
│                                                       │                      │
│                                                       ▼                      │
│                                     ┌────────────────────────────────────┐  │
│                                     │  PLATFORM-LAMBDAS                  │  │
│                                     │                                    │  │
│                                     │  Consome:                          │  │
│                                     │  - ecr_register_best_model_url     │  │
│                                     └────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Guia de Implantacao Completa

### Pre-requisitos

```bash
# Verificar versoes
terraform --version  # >= 1.10.0
aws --version        # v2.x

# Configurar credenciais AWS
aws configure
# ou
export AWS_PROFILE=elo

# Verificar acesso
aws sts get-caller-identity
```

### Passo 1: Foundation

```bash
cd infra/environments/dev/foundation

# Inicializar
terraform init

# Revisar
terraform plan

# Aplicar
terraform apply

# Verificar outputs
terraform output vpc_id
terraform output s3_processed_bucket_id
```

### Passo 2: MLOps (pode ser paralelo com Platform)

```bash
cd ../mlops

terraform init
terraform plan
terraform apply

# Verificar
terraform output mlflow_tracking_uri
```

### Passo 3: Platform

```bash
cd ../platform

terraform init
terraform plan
terraform apply

# Verificar EKS
aws eks describe-cluster --name elo-fraud-cluster-dev --region us-east-1
terraform output eks_kubeconfig_command

# Configurar kubectl
aws eks update-kubeconfig --name elo-fraud-cluster-dev --region us-east-1
kubectl get nodes
```

### Passo 4: Platform-K8s

```bash
cd ../platform-k8s

terraform init
terraform plan
terraform apply

# Verificar
kubectl get pods -A
kubectl get hpa -n fraud-detection
helm list -A
```

### Passo 5: Platform-Lambdas

```bash
# Primeiro, build e push da imagem Docker
cd ../../../../lambdas/register-best-model

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

docker build -t elo-fraud-best-model-register-dev .
docker tag elo-fraud-best-model-register-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest
docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

# Depois, aplicar Terraform
cd ../../infra/environments/dev/platform-lambdas

terraform init
terraform plan
terraform apply
```

### Verificacao Final

```bash
# API Gateway
curl $(cd ../platform && terraform output -raw api_gateway_health_endpoint)

# EKS
kubectl get pods -n fraud-detection

# SQS
aws sqs get-queue-attributes \
  --queue-url $(cd ../platform && terraform output -raw sqs_queue_url) \
  --attribute-names ApproximateNumberOfMessages

# DynamoDB
aws dynamodb describe-table \
  --table-name elo-fraud-customer-recent-tx-dev \
  --query 'Table.TableStatus'
```

---

## Custos Estimados

### Resumo Mensal (DEV)

| Stack | Principais Recursos | Custo Estimado |
|-------|---------------------|----------------|
| **Foundation** | VPC, S3, VPC Endpoints | ~$50 |
| **MLOps** | MLflow (Small), Studio | ~$40 |
| **Platform** | EKS, ALB, NLB, API GW, DynamoDB, SQS, Firehose | ~$165 |
| **Platform-K8s** | Helm charts (custo no node) | $0 |
| **Platform-Lambdas** | Lambda invocations | ~$1 |
| | **Total Estimado** | **~$256/mes** |

### Detalhamento por Servico

| Servico | Quantidade | Custo Estimado |
|---------|------------|----------------|
| EKS Control Plane | 1 | $73 |
| EC2 (t3.medium) | 1 | ~$30 |
| ALB | 1 | ~$16 |
| NLB | 1 | ~$18 |
| VPC Endpoints | 11 | ~$35 |
| S3 | 7 buckets | ~$5 |
| MLflow | Small | ~$35 |
| DynamoDB | On-demand | ~$2 |
| Outros | API GW, SQS, Firehose, etc | ~$42 |

### Otimizacoes Aplicadas

| Otimizacao | Economia Estimada |
|------------|-------------------|
| NAT Gateway desabilitado | ~$32/mes |
| EKS 1 node (vs 3) | ~$60/mes |
| DynamoDB on-demand | Pay-per-use |
| Studio idle shutdown | Variavel |
| Firehose buffer minimo | Entrega rapida |

---

## Diferencas para Outros Ambientes

### DEV vs STAGING

| Aspecto | DEV | STAGING |
|---------|-----|---------|
| **Regiao** | us-east-1 | sa-east-1 |
| **VPC CIDR** | 10.0.0.0/16 | 10.1.0.0/16 |
| **EKS max nodes** | 3 | 5 |
| **HPA max replicas** | 6 | 10 |
| **KEDA max replicas** | 5 | 8 |
| **Proposito** | Desenvolvimento | Pre-producao, testes de carga |

### DEV vs PROD (Planejado)

| Aspecto | DEV | PROD |
|---------|-----|------|
| **Alta Disponibilidade** | 2 AZs, 1 node | 3 AZs, 3+ nodes |
| **TLS/HTTPS** | Desabilitado | Habilitado |
| **WAF** | Desabilitado | Habilitado |
| **Deletion Protection** | Desabilitado | Habilitado |
| **KMS** | AWS Managed | Customer Managed |

---

## Operacoes

### Destruir Ambiente Completo

**ATENCAO:** Destruir na ordem inversa da implantacao!

```bash
# 1. Platform-Lambdas
cd infra/environments/dev/platform-lambdas
terraform destroy

# 2. Platform-K8s
cd ../platform-k8s
terraform destroy

# 3. Platform
cd ../platform
# Esvaziar buckets S3 primeiro
aws s3 rm s3://aws-glue-assets-888577064416-us-east-1 --recursive
terraform destroy

# 4. MLOps
cd ../mlops
terraform destroy

# 5. Foundation
cd ../foundation
# Esvaziar buckets S3 primeiro
aws s3 rm s3://elo-fraud-data-raw-dev-888577064416 --recursive
aws s3 rm s3://elo-fraud-data-processed-dev-888577064416 --recursive
aws s3 rm s3://elo-fraud-models-dev-888577064416 --recursive
aws s3 rm s3://elo-fraud-logs-dev-888577064416 --recursive
terraform destroy
```

### Atualizar Todas as Stacks

```bash
# Script para atualizar todas as stacks em ordem
cd infra/environments/dev

for stack in foundation mlops platform platform-k8s platform-lambdas; do
  echo "=== Updating $stack ==="
  cd $stack
  terraform init -upgrade
  terraform plan
  terraform apply -auto-approve
  cd ..
done
```

### Verificar Estado de Todas as Stacks

```bash
cd infra/environments/dev

for stack in foundation mlops platform platform-k8s platform-lambdas; do
  echo "=== $stack ==="
  cd $stack
  terraform state list | wc -l
  echo "Resources: $(terraform state list | wc -l)"
  cd ..
done
```

---

## Troubleshooting

### Erro: Remote State nao encontrado

**Sintoma:**
```
Error: Unable to find remote state
```

**Causa:** Stack dependente nao foi aplicada.

**Solucao:**
```bash
# Verificar se stack dependente foi aplicada
cd ../foundation  # ou mlops, platform
terraform state list

# Se vazio, aplicar primeiro
terraform apply
```

### Erro: EKS cluster nao acessivel

**Sintoma:**
```
Unable to connect to the server
```

**Solucao:**
```bash
# Reconfigurar kubectl
aws eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --region us-east-1

# Verificar conectividade
kubectl cluster-info
```

### Erro: VPC Endpoint nao funciona

**Sintoma:**
Pods nao conseguem acessar servicos AWS (ECR, S3, etc.)

**Solucao:**
```bash
# Verificar VPC Endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'VpcEndpoints[*].[ServiceName,State]' \
  --output table

# Verificar Security Groups dos endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'VpcEndpoints[*].Groups'
```

### Erro: S3 Bucket nao pode ser deletado

**Sintoma:**
```
BucketNotEmpty: The bucket you tried to delete is not empty
```

**Solucao:**
```bash
# Esvaziar bucket primeiro
aws s3 rm s3://BUCKET_NAME --recursive

# Deletar versoes antigas (se versionado)
aws s3api delete-objects \
  --bucket BUCKET_NAME \
  --delete "$(aws s3api list-object-versions \
    --bucket BUCKET_NAME \
    --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}')"

# Tentar destroy novamente
terraform destroy
```

### Erro: Helm release falha

**Sintoma:**
```
Error: failed to install/upgrade chart
```

**Solucao:**
```bash
# Verificar releases existentes
helm list -A

# Se necessario, deletar release manualmente
helm uninstall RELEASE_NAME -n NAMESPACE

# Re-aplicar
terraform apply
```

---

## Documentacao das Stacks

Para documentacao detalhada de cada stack, consulte:

| Stack | README |
|-------|--------|
| Foundation | [foundation/README.md](./foundation/README.md) |
| MLOps | [mlops/README.md](./mlops/README.md) |
| Platform | [platform/README.md](./platform/README.md) |
| Platform-K8s | [platform-k8s/README.md](./platform-k8s/README.md) |
| Platform-Lambdas | [platform-lambdas/README.md](./platform-lambdas/README.md) |

