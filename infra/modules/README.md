# Terraform Modules

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura de Modulos](#arquitetura-de-modulos)
- [Catalogo de Modulos](#catalogo-de-modulos)
  - [Rede](#rede)
  - [Computacao](#computacao)
  - [API e Integracao](#api-e-integracao)
  - [Dados e Storage](#dados-e-storage)
  - [ETL e Streaming](#etl-e-streaming)
  - [Machine Learning](#machine-learning)
  - [IA Generativa](#ia-generativa)
- [Fluxo de Dados](#fluxo-de-dados)
- [Dependencias entre Modulos](#dependencias-entre-modulos)
- [Como Usar os Modulos](#como-usar-os-modulos)
- [Convencoes](#convencoes)
- [Custos Estimados](#custos-estimados)
- [Limitacoes SCP](#limitacoes-scp)

---

## Visao Geral

Este diretorio contem os **modulos Terraform reutilizaveis** que encapsulam recursos AWS para o sistema de deteccao de fraude. Cada modulo representa uma unidade funcional da infraestrutura.

### Por que Modulos?

| Beneficio | Descricao |
|-----------|-----------|
| **Reutilizacao** | Mesmo modulo usado em dev, staging e prod com configuracoes diferentes |
| **Consistencia** | Garante que recursos sigam os mesmos padroes em todos os ambientes |
| **Abstracao** | Esconde complexidade interna, expondo apenas variaveis relevantes |
| **Manutencao** | Correcoes e melhorias propagam automaticamente para todos os ambientes |
| **Documentacao** | Cada modulo tem seu proprio README com instrucoes detalhadas |

### Estrutura de Modulos

```
infra/modules/
├── README.md                 # Este arquivo (indice geral)
├── vpc/                      # Rede e conectividade
├── alb/                      # Application Load Balancer
├── nlb/                      # Network Load Balancer
├── api-gateway/              # API Gateway REST
├── eks/                      # Kubernetes (EKS)
├── ecr/                      # Container Registry
├── lambda/                   # Funcoes serverless
├── sqs/                      # Filas de mensagens
├── dynamodb/                 # Feature Store
├── s3/                       # Data Lake (buckets)
├── athena/                   # Queries SQL
├── glue/                     # Catalogo e ETL
├── firehose/                 # Streaming de dados
├── sagemaker-studio/         # Ambiente ML
├── mlflow/                   # Tracking de modelos
└── bedrock-agent/            # Agentes IA
```

---

## Arquitetura de Modulos

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SISTEMA DE DETECCAO DE FRAUDE                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ENTRADA                                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   Elo Cartoes ───► API Gateway ───► VPC Link ───► NLB ───► ALB          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                      │
│   PROCESSAMENTO                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                              VPC (Rede Privada)                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │                         EKS (Kubernetes)                           │  │   │
│   │  │                                                                    │  │   │
│   │  │   ┌─────────────────┐          ┌─────────────────┐                │  │   │
│   │  │   │ Inference Pods  │          │  Process Pods   │                │  │   │
│   │  │   │                 │          │                 │                │  │   │
│   │  │   │  - Score API    │          │  - SQS Consumer │                │  │   │
│   │  │   │  - Health Check │          │  - ETL Pipeline │                │  │   │
│   │  │   │                 │          │                 │                │  │   │
│   │  │   └────────┬────────┘          └────────┬────────┘                │  │   │
│   │  │            │                            │                          │  │   │
│   │  └────────────┼────────────────────────────┼──────────────────────────┘  │   │
│   │               │                            │                              │   │
│   │   ┌───────────▼───────────┐    ┌──────────▼──────────┐                   │   │
│   │   │      DynamoDB         │    │        SQS          │                   │   │
│   │   │   (Feature Store)     │    │   (Fila Feedback)   │                   │   │
│   │   └───────────────────────┘    └─────────────────────┘                   │   │
│   │                                                                           │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   DADOS E ML                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐        │   │
│   │   │    S3     │   │  Firehose │   │   Glue    │   │  Athena   │        │   │
│   │   │Data Lake  │◄──│ Streaming │   │  Catalog  │──►│  Queries  │        │   │
│   │   └───────────┘   └───────────┘   └───────────┘   └───────────┘        │   │
│   │         │                                                                │   │
│   │         ▼                                                                │   │
│   │   ┌───────────┐   ┌───────────┐   ┌───────────┐                        │   │
│   │   │ SageMaker │──►│  MLflow   │──►│  Models   │                        │   │
│   │   │  Studio   │   │ Tracking  │   │ Registry  │                        │   │
│   │   └───────────┘   └───────────┘   └───────────┘                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Catalogo de Modulos

### Rede

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[vpc](./vpc/)** | Rede privada virtual isolada | VPC, Subnets, IGW, NAT, VPC Endpoints, Security Groups |
| **[alb](./alb/)** | Application Load Balancer | ALB, Target Group, Listener, Health Checks |
| **[nlb](./nlb/)** | Network Load Balancer para VPC Link | NLB interno, Target Group tipo ALB |

#### VPC

Infraestrutura de rede isolada com subnets publicas/privadas distribuidas em multiplas AZs.

```hcl
module "vpc" {
  source = "../../modules/vpc"

  project_name         = "elo-fraud"
  environment          = "dev"
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

  enable_vpc_endpoints       = true   # S3, DynamoDB (gratuitos)
  enable_interface_endpoints = true   # ECR, SQS, STS, etc.
}
```

#### ALB

Application Load Balancer para roteamento de trafego HTTP/HTTPS para pods EKS.

```hcl
module "alb" {
  source = "../../modules/alb"

  name               = "elo-fraud-alb-dev"
  project_name       = "elo-fraud"
  environment        = "dev"
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.vpc.security_group_alb_id]
  internal           = false
}
```

#### NLB

Network Load Balancer interno para integracao com VPC Link do API Gateway.

```hcl
module "nlb" {
  source = "../../modules/nlb"

  project_name = "elo-fraud"
  environment  = "dev"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
  alb_arn      = module.alb.alb_arn
}
```

---

### Computacao

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[eks](./eks/)** | Cluster Kubernetes gerenciado | EKS Cluster, Node Groups, Addons, IAM Roles |
| **[ecr](./ecr/)** | Container Registry privado | Repositorios ECR, Lifecycle Policies |
| **[lambda](./lambda/)** | Funcoes serverless | Lambda Functions (Zip ou Container) |

#### EKS

Cluster Kubernetes gerenciado para execucao dos servicos de inferencia e processamento.

```hcl
module "eks" {
  source = "../../modules/eks"

  cluster_name    = "elo-fraud-cluster-dev"
  cluster_version = "1.32"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  environment     = "dev"

  node_instance_types = ["t3.medium"]
  node_min_size       = 1
  node_max_size       = 3
}
```

#### ECR

Repositorios Docker privados para imagens dos servicos.

```hcl
module "ecr" {
  source = "../../modules/ecr"

  project_name = "elo-fraud"
  environment  = "dev"
  repositories = ["inference", "process"]
}
```

#### Lambda

Funcoes serverless para processamento event-driven.

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name = "elo-fraud"
  environment  = "dev"
  purpose      = "etl"
  runtime      = "python3.11"
  handler      = "handler.lambda_handler"
  source_path  = "${path.root}/../../services/lambda/etl"
}
```

---

### API e Integracao

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[api-gateway](./api-gateway/)** | Gateway REST para APIs publicas | REST API, Stages, Usage Plans, API Keys, VPC Link |
| **[sqs](./sqs/)** | Filas de mensagens FIFO | SQS Queue, DLQ, CloudWatch Alarms |

#### API Gateway

Gateway REST que expoe endpoints publicos com rate limiting e integracao privada.

```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  project_name = "elo-fraud"
  environment  = "dev"
  stage_name   = "v1"

  # Integracao via VPC Link (privado)
  enable_vpc_link = true
  nlb_arn         = module.nlb.nlb_arn
  nlb_dns_name    = module.nlb.dns_name

  # Usage Plan com API Keys
  enable_usage_plan = true
  api_keys = {
    "elo-backend" = { enabled = true, description = "Backend key" }
  }
}
```

#### SQS

Fila FIFO para processamento assincrono de feedback de transacoes.

```hcl
module "sqs" {
  source = "../../modules/sqs"

  project_name = "elo-fraud"
  environment  = "dev"
  # Nome padrao: {project_name}-transactions-{environment}.fifo

  fifo_queue                  = true
  content_based_deduplication = true
  enable_dlq                  = true
}
```

---

### Dados e Storage

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[dynamodb](./dynamodb/)** | Feature Store NoSQL | Tabela PAY_PER_REQUEST, Encryption |
| **[s3](./s3/)** | Data Lake (buckets) | Buckets Raw/Processed/Models/Logs, Lifecycle |
| **[athena](./athena/)** | Queries SQL sobre S3 | Workgroup, Catalog Database |

#### DynamoDB

Feature Store para armazenar transacoes recentes por cliente.

```hcl
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = "elo-fraud"
  environment  = "dev"
}
```

#### S3

Buckets para Data Lake com dados brutos, processados e modelos ML.

```hcl
module "s3" {
  source = "../../modules/s3"

  project_name      = "elo-fraud"
  environment       = "dev"
  enable_versioning = true

  raw_retention_days       = 90
  processed_retention_days = 180
  logs_retention_days      = 90
}
```

#### Athena

Workgroup para queries SQL sobre dados historicos no S3.

```hcl
module "athena" {
  source = "../../modules/athena"

  project_name        = "elo-fraud"
  environment         = "dev"
  output_bucket_name  = module.s3.processed_bucket_id
  output_prefix       = "query_results/athena/"
}
```

---

### ETL e Streaming

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[glue](./glue/)** | Catalogo de dados e ETL | Glue Database, IAM Role |
| **[firehose](./firehose/)** | Streaming de dados para S3 | Delivery Stream, Buffering, Particionamento |

#### Glue

Catalogo de dados para tabelas do Data Lake.

```hcl
module "glue" {
  source = "../../modules/glue"

  project_name    = "elo-fraud"
  environment     = "dev"
  create_database = true
}
```

#### Firehose

Streaming de dados em tempo real para S3 com particionamento automatico.

```hcl
module "firehose" {
  source = "../../modules/firehose"

  project_name   = "elo-fraud"
  environment    = "dev"
  stream_suffix  = "transactions"
  s3_bucket_arn  = module.s3.raw_bucket_arn
  s3_prefix      = "landing_zone"

  buffer_size_mb          = 5
  buffer_interval_seconds = 60
}
```

---

### Machine Learning

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[sagemaker-studio](./sagemaker-studio/)** | Ambiente de desenvolvimento ML | Domain, User Profile, Apps |
| **[mlflow](./mlflow/)** | Tracking de experimentos e modelos | MLflow Tracking Server |

#### SageMaker Studio

Ambiente integrado para cientistas de dados desenvolverem modelos.

```hcl
module "sagemaker_studio" {
  source = "../../modules/sagemaker-studio"

  project_name = "elo-fraud"
  environment  = "dev"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
}
```

#### MLflow

Tracking server para rastreamento de experimentos e registro de modelos.

```hcl
module "mlflow" {
  source = "../../modules/mlflow"

  project_name       = "elo-fraud"
  environment        = "dev"
  artifact_bucket_id = module.s3.models_bucket_id
}
```

---

### IA Generativa

| Modulo | Descricao | Recursos Principais |
|--------|-----------|---------------------|
| **[bedrock-agent](./bedrock-agent/)** | Agentes de IA com acesso a dados | IAM Role para Bedrock Agents |

#### Bedrock Agent

IAM Role para agentes de IA que consultam dados via Athena.

```hcl
module "bedrock_agent" {
  source = "../../modules/bedrock-agent"

  project_name = "elo-fraud"
  environment  = "dev"
}
```

---

## Fluxo de Dados

### Fluxo Sincrono (Autorizacao de Compra)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   FLUXO SINCRONO - POST /v1/authorize-purchase                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   1. Elo Cartoes                                                                 │
│      │                                                                           │
│      ▼                                                                           │
│   2. API Gateway ─────► Rate Limiting, API Key Validation                        │
│      │                                                                           │
│      ▼                                                                           │
│   3. VPC Link ────────► Conexao privada (nao passa pela internet)                │
│      │                                                                           │
│      ▼                                                                           │
│   4. NLB ─────────────► Layer 4 load balancing                                   │
│      │                                                                           │
│      ▼                                                                           │
│   5. ALB ─────────────► Layer 7 routing, health checks                           │
│      │                                                                           │
│      ▼                                                                           │
│   6. EKS (Inference) ─► Consulta DynamoDB (features) + MLflow (modelo)          │
│      │                                                                           │
│      ▼                                                                           │
│   7. Response ────────► Score de fraude (0-100) + latencia < 500ms               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo Assincrono (Feedback)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO ASSINCRONO - Feedback TE40 via SQS                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   1. Elo Cartoes (TE40)                                                          │
│      │                                                                           │
│      ▼                                                                           │
│   2. SQS FIFO (direto) ► Cliente envia mensagem diretamente para fila via SDK    │
│      │                                                                           │
│      ▼                                                                           │
│   3. SQS FIFO ────────► Ordenacao garantida, deduplicacao                        │
│      │                                                                           │
│      ▼                                                                           │
│   4. EKS (Process) ───► Consome mensagens em batch                               │
│      │                                                                           │
│      ├──► DynamoDB ───► Atualiza fraud_label na transacao                        │
│      │                                                                           │
│      └──► Firehose ───► Streaming para S3 (historico)                            │
│               │                                                                  │
│               ▼                                                                  │
│           S3 (Raw) ───► Dados para retreino do modelo                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Treinamento (ML)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE TREINAMENTO ML                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   1. S3 (Raw/Processed)                                                          │
│      │                                                                           │
│      ▼                                                                           │
│   2. Glue Catalog ────► Metadados das tabelas                                    │
│      │                                                                           │
│      ▼                                                                           │
│   3. SageMaker Studio ► Notebook para exploracao e feature engineering           │
│      │                                                                           │
│      ▼                                                                           │
│   4. Athena ──────────► Queries SQL para analise exploratoria                    │
│      │                                                                           │
│      ▼                                                                           │
│   5. Training Job ────► Treinamento do modelo                                    │
│      │                                                                           │
│      ▼                                                                           │
│   6. MLflow ──────────► Registro de experimentos e metricas                      │
│      │                                                                           │
│      ▼                                                                           │
│   7. Model Registry ──► Modelo registrado para deploy                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Dependencias entre Modulos

### Ordem de Criacao

Os modulos devem ser criados na seguinte ordem para respeitar dependencias:

```
Nivel 1 (Base):
├── vpc           # Nenhuma dependencia
├── s3            # Nenhuma dependencia
└── ecr           # Nenhuma dependencia

Nivel 2 (Computacao):
├── eks           # Depende: vpc
├── dynamodb      # Nenhuma dependencia
├── sqs           # Nenhuma dependencia
└── glue          # Depende: s3

Nivel 3 (Load Balancers):
├── alb           # Depende: vpc, eks
└── firehose      # Depende: s3

Nivel 4 (Integracao):
├── nlb           # Depende: vpc, alb
└── athena        # Depende: s3, glue

Nivel 5 (API):
└── api-gateway   # Depende: alb, nlb, sqs

Nivel 6 (ML):
├── sagemaker-studio  # Depende: vpc, s3
├── mlflow            # Depende: s3
└── bedrock-agent     # Nenhuma dependencia

Nivel 7 (Serverless):
└── lambda        # Depende: s3, sqs, dynamodb (conforme uso)
```

### Matriz de Dependencias

| Modulo | Depende de |
|--------|------------|
| `vpc` | - |
| `s3` | - |
| `ecr` | - |
| `dynamodb` | - |
| `sqs` | - |
| `glue` | `s3` |
| `eks` | `vpc` |
| `alb` | `vpc` |
| `nlb` | `vpc`, `alb` |
| `firehose` | `s3` |
| `athena` | `s3`, `glue` |
| `api-gateway` | `alb`, `nlb` (opcional), `sqs` |
| `sagemaker-studio` | `vpc`, `s3` |
| `mlflow` | `s3` |
| `bedrock-agent` | - |
| `lambda` | Varia conforme uso |

---

## Como Usar os Modulos

### 1. Referencia Local

```hcl
module "vpc" {
  source = "../../modules/vpc"

  # Variaveis obrigatorias
  project_name = "elo-fraud"
  environment  = "dev"
  # ...
}
```

### 2. Passando Outputs entre Modulos

```hcl
module "vpc" {
  source = "../../modules/vpc"
  # ...
}

module "eks" {
  source = "../../modules/eks"

  vpc_id     = module.vpc.vpc_id                 # Output do modulo VPC
  subnet_ids = module.vpc.private_subnet_ids     # Output do modulo VPC
  # ...
}

module "alb" {
  source = "../../modules/alb"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.vpc.security_group_alb_id]
  # ...
}
```

### 3. Usando Data Sources

```hcl
# Buscar recursos existentes
data "aws_vpc" "existing" {
  tags = {
    Name = "elo-fraud-vpc-dev"
  }
}

module "eks" {
  source = "../../modules/eks"

  vpc_id = data.aws_vpc.existing.id
  # ...
}
```

---

## Convencoes

### Nomenclatura de Recursos

```
{project_name}-{recurso}-{environment}

Exemplos:
- elo-fraud-vpc-dev
- elo-fraud-alb-staging
- elo-fraud-cluster-prod
- elo-fraud-api-dev
```

### Estrutura de Modulo

Cada modulo deve conter:

```
modulo/
├── README.md       # Documentacao completa
├── main.tf         # Recursos principais
├── variables.tf    # Variaveis de entrada
├── outputs.tf      # Valores de saida
└── versions.tf     # Versoes de providers (opcional)
```

### Variaveis Padrao

Todos os modulos devem aceitar:

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `project_name` | `string` | Nome do projeto |
| `environment` | `string` | Ambiente (dev, staging, prod) |
| `tags` | `map(string)` | Tags adicionais |

### Tags Padrao

```hcl
tags = {
  Project     = var.project_name
  Environment = var.environment
  ManagedBy   = "terraform"
  Component   = "nome-do-modulo"
}
```

---

## Custos Estimados

### Por Modulo (sa-east-1)

| Modulo | Componente Principal | Custo Estimado/Mes |
|--------|---------------------|-------------------|
| `vpc` | VPC + Gateway Endpoints | $0 |
| `vpc` | Interface Endpoints (9x2 AZs) | ~$130 |
| `vpc` | NAT Gateway (opcional) | ~$32 + dados |
| `alb` | Application Load Balancer | ~$20 + LCUs |
| `nlb` | Network Load Balancer | ~$20 + LCUs |
| `eks` | Control Plane | ~$73 |
| `eks` | Nodes (1-3x t3.medium) | ~$30-90 |
| `ecr` | Repositorios | ~$0.10/GB |
| `api-gateway` | REST API | ~$3.50/milhao requests |
| `sqs` | Fila FIFO | ~$0.50/milhao requests |
| `dynamodb` | On-Demand | ~$1.25/milhao WCUs |
| `s3` | Standard Storage | ~$0.023/GB |
| `athena` | Queries | ~$5/TB escaneado |
| `firehose` | Streaming | ~$0.029/GB |
| `sagemaker-studio` | ml.t3.medium | ~$0.05/hora |
| `mlflow` | Tracking Server | ~$30 |

### Custo Total Estimado por Ambiente

| Ambiente | Descricao | Custo Estimado |
|----------|-----------|----------------|
| **DEV** | Minimo, sem NAT, 1-3 nodes t3.medium | ~$250-400/mes |
| **STAGING** | Com Interface Endpoints, 1-5 nodes t3.medium | ~$300-700/mes |
| **PROD** | HA completo, 3-10 nodes t3.large, NAT | ~$800-1200/mes |

---

## Limitacoes SCP

A conta AWS possui **Service Control Policies (SCPs)** que bloqueiam certas acoes. Os modulos foram ajustados para funcionar com essas restricoes:

### Acoes Bloqueadas

| Acao | Impacto | Workaround |
|------|---------|------------|
| `iam:TagRole` | Nao pode aplicar tags em IAM roles | Tags removidas de roles |
| `iam:CreatePolicy` | Nao pode criar custom policies | Usar AWS managed policies |
| `iam:CreateOpenIDConnectProvider` | Nao pode criar OIDC provider | IRSA desabilitado no EKS |
| `s3:PutBucketPublicAccessBlock` | Nao pode configurar public access | Buckets privados por padrao |

### Modulos Afetados

| Modulo | Ajustes |
|--------|---------|
| `eks` | IRSA desabilitado, pods usam role do node |
| `s3` | Public access block comentado |
| `glue` | Tags em IAM role removidas |
| `firehose` | Tags em IAM role ignoradas |
| `lambda` | Tags em IAM role ignoradas |
| `bedrock-agent` | Tags em IAM role removidas |

Para detalhes, consulte `infra/bootstrap/LIMITACAO_SCP.md`.

---

## Referencias

### Documentacao AWS

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Solutions Library](https://aws.amazon.com/solutions/)

### Documentacao do Projeto

- [Arquitetura Geral](../../docs/ARCHITECTURE_OVERVIEW.md)
- [Guia de Troubleshooting](../../docs/TROUBLESHOOTING.md)
- [Guia de Testes E2E](../../docs/E2E_TESTING_GUIDE.md)

### Modulos Externos

- [terraform-aws-modules/eks](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [terraform-aws-modules/vpc](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest)
