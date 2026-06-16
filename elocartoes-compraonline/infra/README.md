# Infraestrutura

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Estrutura de Diretorios](#estrutura-de-diretorios)
- [Ambientes](#ambientes)
- [Stacks](#stacks)
- [Ordem de Deploy](#ordem-de-deploy)
- [Pre-requisitos](#pre-requisitos)
- [Quick Start](#quick-start)
- [Operacoes](#operacoes)
- [Servicos AWS](#servicos-aws)
- [Custos Estimados](#custos-estimados)
- [Troubleshooting](#troubleshooting)
- [Limitacoes SCP](#limitacoes-scp)
- [Referencias](#referencias)

---

## Visao Geral

Este diretorio contem o codigo **Terraform** que provisiona toda a infraestrutura AWS do sistema de deteccao de fraudes em tempo real.

### Proposito do Sistema

| Funcao | Descricao |
|--------|-----------|
| **Scoring de Fraude** | Analisa transacoes em tempo real e retorna score de risco |
| **SLA** | p95 < 500ms para respostas de scoring |
| **Feedback Loop** | Recebe confirmacao de fraude para retreino do modelo |
| **Data Lake** | Armazena dados historicos para analytics e ML |

### Fluxos Principais

| Fluxo | Endpoint | Descricao |
|-------|----------|-----------|
| **Sincrono** | `POST /v1/authorize-purchase` | Autorizacao de compra em tempo real de transacoes 3DS (via API Gateway) |
| **Assincrono** | `SQS FIFO` | Recebimento de feedback TE40 para retreino (cliente envia direto para fila) |

### Caracteristicas

| Aspecto | Valor |
|---------|-------|
| **IaC Tool** | Terraform >= 1.10.0 |
| **Cloud Provider** | AWS |
| **Regioes** | DEV: us-east-1, STAGING/PROD: sa-east-1 |
| **Ambientes** | DEV, STAGING, (PROD futuro) |
| **State Backend** | S3 com locking nativo |

---

## Arquitetura

### Visao Geral do Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SISTEMA DE DETECCAO DE FRAUDE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ENTRADA (Elo Cartoes)                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   POST /v1/authorize-purchase ──► API Gateway ──► VPC Link ──► NLB      │   │
│   │   Feedback TE40 ─────► SQS FIFO (direto) ─────► EKS Process            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                      │
│   VPC (Rede Privada)                      ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │                         EKS CLUSTER                              │   │   │
│   │   │                                                                  │   │   │
│   │   │   ┌─────────────────┐          ┌─────────────────┐              │   │   │
│   │   │   │ Inference Pods  │◄── ALB ──│  Process Pods   │◄── SQS      │   │   │
│   │   │   │                 │          │                 │              │   │   │
│   │   │   │  Score API      │          │  Feedback ETL   │              │   │   │
│   │   │   └────────┬────────┘          └────────┬────────┘              │   │   │
│   │   │            │                            │                        │   │   │
│   │   └────────────┼────────────────────────────┼────────────────────────┘   │   │
│   │                │                            │                            │   │
│   │   ┌────────────▼────────────┐    ┌─────────▼─────────┐                  │   │
│   │   │       DynamoDB          │    │      Firehose     │                  │   │
│   │   │    (Feature Store)      │    │   (Streaming)     │                  │   │
│   │   └─────────────────────────┘    └─────────┬─────────┘                  │   │
│   │                                            │                            │   │
│   │   ┌────────────────────────────────────────▼────────────────────────┐   │   │
│   │   │                         S3 DATA LAKE (7 buckets)                 │   │   │
│   │   │                                                                  │   │   │
│   │   │   Raw ─ Processed ─ Models ─ Logs ─ Resources ─ Reports (2)     │   │   │
│   │   │                                                                  │   │   │
│   │   └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   MACHINE LEARNING                                                               │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   SageMaker Studio ──► MLflow Tracking ──► Model Registry               │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Sincrono (Scoring)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      POST /v1/authorize-purchase (< 500ms)                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Elo ──► API Gateway ──► VPC Link ──► NLB ──► ALB ──► EKS (inference)          │
│                                                              │                   │
│                                                              ├──► DynamoDB       │
│                                                              │    (features)     │
│                                                              │                   │
│                                                              └──► MLflow Model   │
│                                                                   (predicao)    │
│                                                                        │        │
│   Response ◄───────────────────────────────────────────────────────────┘        │
│   { "score": 85, "risk_level": "HIGH" }                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Assincrono (Feedback)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Feedback TE40 (via SQS direto)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Elo ──► SQS FIFO (direto) ──► EKS (process)                                   │
│                                        │                                         │
│                                        ├──► DynamoDB (atualiza label)            │
│                                        │                                         │
│                                        └──► Firehose ──► S3 (historico)          │
│                                                                                  │
│   NOTA: Cliente envia mensagens diretamente para fila SQS via AWS SDK            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretorios

```
infra/
├── README.md                    # Este arquivo (guia principal)
│
├── bootstrap/                   # Estado remoto do Terraform
│   ├── main.tf                  # S3 bucket para state
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example # Exemplo de variaveis
│   └── README.md
│
├── environments/                # Configuracoes por ambiente
│   ├── README.md
│   │
│   ├── dev/                     # Ambiente de Desenvolvimento
│   │   ├── foundation/          # VPC, S3 buckets
│   │   ├── mlops/               # MLflow, SageMaker Studio
│   │   ├── platform/            # EKS, API Gateway, DynamoDB, SQS
│   │   ├── platform-k8s/        # Manifests Kubernetes
│   │   └── platform-lambdas/    # Lambda functions
│   │
│   └── staging/                 # Ambiente de Staging
│       ├── foundation/
│       ├── mlops/
│       ├── platform/
│       ├── platform-k8s/
│       └── platform-lambdas/
│
└── modules/                     # Componentes reutilizaveis
    ├── README.md                # Catalogo de modulos
    ├── vpc/
    ├── alb/
    ├── nlb/
    ├── api-gateway/
    ├── eks/
    ├── ecr/
    ├── lambda/
    ├── sqs/
    ├── dynamodb/
    ├── s3/
    ├── athena/
    ├── glue/
    ├── firehose/
    ├── sagemaker-studio/
    ├── mlflow/
    └── bedrock-agent/
```

---

## Ambientes

### Configuracao por Ambiente

| Ambiente | Regiao | VPC CIDR | Descricao |
|----------|--------|----------|-----------|
| **DEV** | us-east-1 | 10.0.0.0/16 | Desenvolvimento e testes |
| **STAGING** | sa-east-1 | 10.1.0.0/16 | Pre-producao e validacao |
| **PROD** | sa-east-1 | 10.2.0.0/16 | Producao (futuro) |

### Diferencas entre Ambientes

| Aspecto | DEV | STAGING | PROD |
|---------|-----|---------|------|
| **Regiao** | us-east-1 | sa-east-1 | sa-east-1 |
| **EKS Nodes** | 1-3 | 1-5 | 3-10 (HA) |
| **Instance Type** | t3.medium | t3.medium | t3.large |
| **NAT Gateway** | Nao | Nao | Sim (HA) |
| **Interface Endpoints** | Opcional | Sim | Sim |
| **Backups** | Opcional | Sim | Obrigatorio |
| **force_destroy** | true | true | false |

---

## Stacks

A infraestrutura e dividida em **5 stacks independentes** para isolar responsabilidades e permitir deploys parciais.

### Diagrama de Stacks

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    STACKS                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                            FOUNDATION                                    │   │
│   │                                                                          │   │
│   │   VPC ─── Subnets ─── Internet Gateway ─── VPC Endpoints                │   │
│   │                                                                          │   │
│   │   S3: Raw ─ Processed ─ Models ─ Logs ─ Resources ─ Reports (2)        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                          │
│           ┌───────────────────────────┼───────────────────────────┐             │
│           │                           │                           │             │
│           ▼                           ▼                           ▼             │
│   ┌───────────────┐      ┌─────────────────────┐      ┌───────────────────┐    │
│   │     MLOPS     │      │      PLATFORM       │      │  PLATFORM-LAMBDAS │    │
│   │               │      │                     │      │                   │    │
│   │ MLflow        │      │ EKS ─── ECR ─── ALB │      │ register-best-    │    │
│   │ SageMaker     │      │ NLB ─── API Gateway │      │ model (Lambda)    │    │
│   │ Studio        │      │ DynamoDB ─── SQS    │      │                   │    │
│   │               │      │ Athena ─── Glue     │      │                   │    │
│   │               │      │ Firehose            │      │                   │    │
│   └───────────────┘      └──────────┬──────────┘      └───────────────────┘    │
│                                     │                                           │
│                                     ▼                                           │
│                          ┌───────────────────┐                                  │
│                          │   PLATFORM-K8S    │                                  │
│                          │                   │                                  │
│                          │ Deployments       │                                  │
│                          │ Services          │                                  │
│                          │ ConfigMaps        │                                  │
│                          │ Secrets           │                                  │
│                          └───────────────────┘                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Descricao das Stacks

#### 1. Foundation

Camada base da infraestrutura. **Muda raramente**.

| Recurso | Modulo | Descricao |
|---------|--------|-----------|
| VPC | `vpc` | Rede isolada com subnets publicas/privadas |
| VPC Endpoints | `vpc` | Acesso privado a servicos AWS |
| S3 Buckets | `s3` | Data Lake (7 buckets: raw, processed, models, logs, resources, reports_promotion, reports_statistics) |

#### 2. MLOps

Ferramentas para ciclo de vida de ML. Usada pelo **time de Data Science**.

| Recurso | Modulo | Descricao |
|---------|--------|-----------|
| MLflow | `mlflow` | Tracking de experimentos e modelos |
| SageMaker Studio | `sagemaker-studio` | IDE para desenvolvimento ML |

#### 3. Platform

Stack principal da aplicacao. **Muda frequentemente**.

| Recurso | Modulo | Descricao |
|---------|--------|-----------|
| EKS | `eks` | Cluster Kubernetes |
| ECR | `ecr` | Repositorios Docker |
| ALB | `alb` | Application Load Balancer |
| NLB | `nlb` | Network Load Balancer (VPC Link) |
| API Gateway | `api-gateway` | REST API publica |
| DynamoDB | `dynamodb` | Feature Store |
| SQS | `sqs` | Fila FIFO para feedback |
| Athena | `athena` | SQL analytics |
| Glue | `glue` | Catalogo de dados |
| Firehose | `firehose` | Streaming para S3 |

#### 4. Platform-K8s

Recursos Kubernetes gerenciados via Terraform (Helm charts e CRDs).

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| Namespace | K8s | fraud-detection namespace |
| Helm Charts | Helm | Metrics Server, Cluster Autoscaler, AWS LB Controller, KEDA |
| ConfigMaps | K8s | inference-config, process-config |
| HPA | K8s | Autoscaling CPU-based para inference |
| ScaledObject | KEDA | Autoscaling SQS-based para process |
| PDBs | K8s | PodDisruptionBudgets para alta disponibilidade |
| TargetGroupBinding | CRD | Integracao Service K8s com ALB Terraform |

#### 5. Platform-Lambdas

Funcoes serverless container-based para automacao MLOps.

| Recurso | Modulo | Descricao |
|---------|--------|-----------|
| register-best-model | `lambda` | Registra melhor modelo do MLflow baseado em f1_score |

---

## Ordem de Deploy

### Diagrama de Dependencias

```
                    1. bootstrap (uma unica vez)
                           │
                           ▼
                    2. foundation
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
      3. mlops        3. platform    3. platform-lambdas
                           │
                           ▼
                    4. platform-k8s
```

### Tabela de Ordem

| Ordem | Stack | Dependencias | Frequencia de Mudanca |
|-------|-------|--------------|----------------------|
| 1 | `bootstrap` | Nenhuma | Uma vez |
| 2 | `foundation` | bootstrap | Raramente |
| 3 | `mlops` | foundation | Ocasional |
| 3 | `platform` | foundation | Frequente |
| 3 | `platform-lambdas` | foundation | Ocasional |
| 4 | `platform-k8s` | platform | Frequente |

---

## Pre-requisitos

### Ferramentas Necessarias

| Ferramenta | Versao Minima | Instalacao |
|------------|---------------|------------|
| **Terraform** | >= 1.10.0 | [terraform.io/downloads](https://terraform.io/downloads) |
| **AWS CLI** | >= 2.0 | [aws.amazon.com/cli](https://aws.amazon.com/cli) |
| **kubectl** | >= 1.31 | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools) |
| **Helm** | >= 3.0 | [helm.sh/docs/intro/install](https://helm.sh/docs/intro/install) |

### Configuracao AWS

```bash
# Configurar credenciais AWS
aws configure

# Verificar identidade
aws sts get-caller-identity

# Verificar regiao
aws configure get region
```

### Permissoes IAM

O usuario/role deve ter permissoes para:

- EC2, VPC, EKS, ECR
- S3, DynamoDB, SQS
- API Gateway, Lambda
- SageMaker, CloudWatch
- IAM (limitado por SCPs)

---

## Quick Start

### 1. Bootstrap (Primeira Vez)

```bash
cd infra/bootstrap

# Inicializar Terraform (backend local temporario)
terraform init

# Criar bucket S3 para state
terraform apply

# Anotar outputs para configurar backends
terraform output
```

### 2. Foundation

```bash
cd infra/environments/dev/foundation

# Inicializar com backend S3
terraform init

# Revisar plano
terraform plan

# Aplicar
terraform apply
```

### 3. Platform

```bash
cd infra/environments/dev/platform

# Inicializar
terraform init

# Aplicar
terraform apply
```

### 4. Configurar kubectl

```bash
# Atualizar kubeconfig
aws eks update-kubeconfig \
  --name elo-fraud-cluster-dev \
  --region us-east-1

# Verificar conexao
kubectl cluster-info
kubectl get nodes
```

---

## Operacoes

### Comandos Terraform Comuns

```bash
# Inicializar (primeira vez ou apos mudanca de backend)
terraform init

# Validar sintaxe
terraform validate

# Formatar codigo
terraform fmt -recursive

# Planejar mudancas
terraform plan -out=tfplan

# Aplicar mudancas
terraform apply tfplan

# Ver estado atual
terraform state list

# Destruir recursos (CUIDADO!)
terraform destroy
```

### Deploy de Stack Especifica

```bash
# Deploy apenas foundation
cd infra/environments/dev/foundation
terraform apply

# Deploy apenas platform
cd infra/environments/dev/platform
terraform apply
```

### Atualizar Modulos

```bash
# Atualizar todos os modulos
terraform init -upgrade

# Verificar versoes de modulos
terraform providers
```

### Ver Outputs

```bash
# Ver outputs de uma stack
terraform output

# Ver output especifico
terraform output vpc_id

# Ver output em formato JSON
terraform output -json
```

### Importar Recursos Existentes

```bash
# Importar recurso existente para o state
terraform import aws_s3_bucket.example bucket-name
```

---

## Servicos AWS

### Catalogo Completo

| Categoria | Servico | Uso no Projeto |
|-----------|---------|----------------|
| **Rede** | VPC | Rede isolada |
| | Subnets | Publicas e privadas |
| | Internet Gateway | Acesso internet |
| | NAT Gateway | Saida privada (opcional) |
| | VPC Endpoints | Acesso privado AWS |
| | ALB | Load balancer HTTP |
| | NLB | Load balancer TCP (VPC Link) |
| **Computacao** | EKS | Kubernetes gerenciado |
| | ECR | Registry Docker |
| | Lambda | Funcoes serverless |
| **API** | API Gateway | REST API publica |
| **Mensageria** | SQS | Filas FIFO |
| **Banco de Dados** | DynamoDB | Feature Store |
| **Armazenamento** | S3 | Data Lake |
| **ETL/Streaming** | Glue | Catalogo de dados |
| | Firehose | Streaming para S3 |
| | Athena | SQL analytics |
| **Machine Learning** | SageMaker Studio | IDE ML |
| | MLflow | Tracking Server |
| **Observabilidade** | CloudWatch Logs | Logs centralizados |
| | CloudWatch Metrics | Metricas |
| | CloudWatch Alarms | Alertas |
| **Seguranca** | IAM | Identidade e acesso |
| | Security Groups | Firewall |
| | KMS | Criptografia |

---

## Custos Estimados

### Por Stack (sa-east-1)

| Stack | Componente Principal | DEV | STAGING | PROD |
|-------|---------------------|-----|---------|------|
| **Foundation** | VPC + S3 | ~$130 | ~$130 | ~$200 |
| **MLOps** | MLflow + Studio | ~$50 | ~$80 | ~$150 |
| **Platform** | EKS + API GW | ~$200 | ~$350 | ~$600 |
| **Platform-Lambdas** | Lambda | ~$5 | ~$10 | ~$30 |
| **TOTAL** | - | **~$385** | **~$570** | **~$980** |

### Detalhamento Foundation

| Recurso | Calculo | Custo/Mes |
|---------|---------|-----------|
| VPC | Gratuito | $0 |
| Gateway Endpoints | Gratuito | $0 |
| Interface Endpoints (9x2 AZs) | $0.01/hora x 9 x 2 x 730 | ~$130 |
| S3 Storage (100GB) | $0.023/GB | ~$2.30 |
| **Total Foundation** | - | **~$132** |

### Detalhamento Platform

| Recurso | Calculo | Custo/Mes |
|---------|---------|-----------|
| EKS Control Plane | $0.10/hora x 730 | ~$73 |
| EKS Nodes (1-3x t3.medium) | 1-3 x $0.0416/h x 730 | ~$30-90 |
| ALB | $0.0225/hora + LCUs | ~$20 |
| NLB | $0.0225/hora + LCUs | ~$20 |
| API Gateway | $3.50/milhao requests | ~$10 |
| DynamoDB (On-Demand) | Variavel | ~$10 |
| SQS FIFO | $0.50/milhao requests | ~$5 |
| Firehose | $0.029/GB | ~$5 |
| **Total Platform** | - | **~$192** |

---

## Troubleshooting

### Erro: State Lock

**Sintoma**: `Error acquiring the state lock`

**Causa**: Lock nao liberado de execucao anterior.

**Solucao**:
```bash
# Terraform 1.10+ usa S3 native locking
# Verificar se existe .tflock file no bucket
aws s3 ls s3://BUCKET_NAME/path/to/state/

# Se necessario, forcar unlock (CUIDADO!)
terraform force-unlock LOCK_ID
```

---

### Erro: Credenciais AWS

**Sintoma**: `Error: No valid credential sources found`

**Solucao**:
```bash
# Verificar credenciais
aws sts get-caller-identity

# Reconfigurar se necessario
aws configure

# Verificar variaveis de ambiente
echo $AWS_PROFILE
echo $AWS_DEFAULT_REGION
```

---

### Erro: Modulo nao encontrado

**Sintoma**: `Error: Module not found`

**Solucao**:
```bash
# Reinicializar modulos
terraform init -upgrade

# Verificar caminho do modulo no source
# source = "../../../modules/vpc"  # Caminho relativo correto
```

---

### Erro: Resource already exists

**Sintoma**: `Error: Resource already exists`

**Solucao**:
```bash
# Importar recurso existente para o state
terraform import aws_s3_bucket.example bucket-name

# Ou remover do state e recriar
terraform state rm aws_s3_bucket.example
terraform apply
```

---

### Erro: Quota exceeded

**Sintoma**: `Error: Service quota exceeded`

**Solucao**:
```bash
# Ver quotas atuais
aws service-quotas list-service-quotas --service-code ec2

# Solicitar aumento via console ou CLI
aws service-quotas request-service-quota-increase \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --desired-value 10
```

---

## Limitacoes SCP

A conta AWS possui **Service Control Policies (SCPs)** que bloqueiam certas acoes:

### Acoes Bloqueadas

| Acao | Impacto | Workaround |
|------|---------|------------|
| `iam:TagRole` | Nao pode aplicar tags em IAM roles | Tags removidas de roles |
| `iam:CreatePolicy` | Nao pode criar custom policies | Usar AWS managed policies |
| `iam:CreateOpenIDConnectProvider` | Nao pode criar OIDC provider | IRSA desabilitado no EKS |
| `s3:PutBucketPublicAccessBlock` | Nao pode configurar public access | Buckets privados por padrao |

### Modulos Afetados

| Modulo | Ajuste Aplicado |
|--------|-----------------|
| `eks` | IRSA desabilitado, pods usam role do node |
| `s3` | Public access block comentado |
| `glue` | Tags em IAM role removidas |
| `firehose` | Tags em IAM role ignoradas |
| `lambda` | Tags em IAM role ignoradas |
| `bedrock-agent` | Tags em IAM role removidas |

Para detalhes completos, consulte `infra/bootstrap/README.md`.

---

## Referencias

### Documentacao do Projeto

| Documento | Descricao |
|-----------|-----------|
| [bootstrap/README.md](bootstrap/README.md) | Estado remoto do Terraform |
| [environments/README.md](environments/README.md) | Organizacao por ambiente |
| [modules/README.md](modules/README.md) | Catalogo de modulos |

### Documentacao Externa

| Recurso | Link |
|---------|------|
| **Terraform AWS Provider** | [registry.terraform.io/providers/hashicorp/aws](https://registry.terraform.io/providers/hashicorp/aws) |
| **AWS Well-Architected** | [aws.amazon.com/architecture/well-architected](https://aws.amazon.com/architecture/well-architected) |
| **EKS Best Practices** | [aws.github.io/aws-eks-best-practices](https://aws.github.io/aws-eks-best-practices) |
| **Terraform Best Practices** | [terraform.io/docs/cloud/guides/recommended-practices](https://terraform.io/docs/cloud/guides/recommended-practices) |

### Documentacao de Servicos AWS

| Servico | Link |
|---------|------|
| VPC | [docs.aws.amazon.com/vpc](https://docs.aws.amazon.com/vpc) |
| EKS | [docs.aws.amazon.com/eks](https://docs.aws.amazon.com/eks) |
| API Gateway | [docs.aws.amazon.com/apigateway](https://docs.aws.amazon.com/apigateway) |
| DynamoDB | [docs.aws.amazon.com/dynamodb](https://docs.aws.amazon.com/dynamodb) |
| S3 | [docs.aws.amazon.com/s3](https://docs.aws.amazon.com/s3) |
| SageMaker | [docs.aws.amazon.com/sagemaker](https://docs.aws.amazon.com/sagemaker) |
