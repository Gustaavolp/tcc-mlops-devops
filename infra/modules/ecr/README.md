# ECR Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Repositorios](#repositorios)
- [Recursos Criados](#recursos-criados)
- [Lifecycle Policies](#lifecycle-policies)
- [Scan de Vulnerabilidades](#scan-de-vulnerabilidades)
- [Cross-Account Access](#cross-account-access)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona repositorios **Amazon ECR (Elastic Container Registry)** para armazenar as imagens Docker dos servicos de deteccao de fraude.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Armazenamento de Imagens** | Repositorios privados para containers Docker |
| **Seguranca** | Scan automatico de vulnerabilidades (CVEs) |
| **Gestao de Ciclo de Vida** | Lifecycle policies para limpeza automatica |
| **Integracao CI/CD** | Push via GitHub Actions, pull via EKS/SageMaker |

### Por que ECR?

| Beneficio | Descricao |
|-----------|-----------|
| **Integracao Nativa** | Pull direto do EKS sem configuracao adicional de credenciais |
| **Scan de Vulnerabilidades** | Detecta CVEs automaticamente em cada push |
| **Lifecycle Policies** | Remove imagens antigas automaticamente, reduzindo custos |
| **Alta Disponibilidade** | Replicacao automatica dentro da regiao |
| **IAM Integration** | Controle de acesso granular via IAM policies |

---

## Arquitetura

```
                              CI/CD Pipeline
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────────────────┐  │
│   │    GitHub     │      │    Docker     │      │           ECR             │  │
│   │    Actions    │─────▶│    Build      │─────▶│                           │  │
│   │               │      │               │      │  ┌─────────────────────┐  │  │
│   └───────────────┘      └───────────────┘      │  │ inference-{env}     │  │  │
│                                                  │  │ (API scoring)       │  │  │
│                                                  │  └─────────────────────┘  │  │
│                                                  │                           │  │
│                                                  │  ┌─────────────────────┐  │  │
│                                                  │  │ process-{env}       │  │  │
│                                                  │  │ (SQS worker)        │  │  │
│                                                  │  └─────────────────────┘  │  │
│                                                  │                           │  │
│                                                  │  ┌─────────────────────┐  │  │
│                                                  │  │ model-{env}         │  │  │
│                                                  │  │ (ML container)      │  │  │
│                                                  │  └─────────────────────┘  │  │
│                                                  │                           │  │
│                                                  └───────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                              Deployment
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ┌───────────────────────────┐                                                │
│   │           ECR             │                                                │
│   │                           │                                                │
│   │  ┌─────────────────────┐  │        ┌───────────────┐                      │
│   │  │ inference-{env}     │──┼───────▶│      EKS      │                      │
│   │  └─────────────────────┘  │        │  (Inference   │                      │
│   │                           │        │   Deployment) │                      │
│   │  ┌─────────────────────┐  │        └───────────────┘                      │
│   │  │ process-{env}       │──┼───────▶│      EKS      │                      │
│   │  └─────────────────────┘  │        │  (Process     │                      │
│   │                           │        │   Deployment) │                      │
│   │  ┌─────────────────────┐  │        └───────────────┘                      │
│   │  │ model-{env}         │──┼───────▶│   SageMaker   │                      │
│   │  └─────────────────────┘  │        │  (Training/   │                      │
│   │                           │        │   Inference)  │                      │
│   └───────────────────────────┘        └───────────────┘                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Repositorios

### Nomenclatura

Os nomes dos repositorios sao definidos **explicitamente** via variaveis:
- `inference_repo_name` - Nome do repositorio de inference
- `process_repo_name` - Nome do repositorio de process
- `model_repo_name` - Nome do repositorio de model

**Convencao recomendada:** `{project_name}-{service}-{environment}`

### Repositorios Disponiveis

#### Servicos Kubernetes (EKS)

| Repositorio | Servico | Descricao | Consumidor |
|-------------|---------|-----------|------------|
| `elo-fraud-inference-{env}` | Inference | API de scoring de fraude em tempo real | EKS |
| `elo-fraud-process-{env}` | Process | Worker assincrono que consome SQS | EKS |
| `elo-fraud-model-{env}` | Model | Container customizado do modelo ML | SageMaker |

#### Lambdas (Container Image)

| Repositorio | Servico | Descricao | Consumidor |
|-------------|---------|-----------|------------|
| `best-model-register-{env}` | Register Best Model | Registra melhor modelo no Model Registry via MLflow | Lambda |
| `etl-delta-filter-{env}` | ETL Delta Filter | Processa dados incrementais usando Delta Lake | Lambda |

### Detalhamento dos Repositorios

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Inference Repository                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Nome: elo-fraud-inference-{env}                                               │
│                                                                                 │
│  Conteudo:                                                                      │
│  - FastAPI application                                                          │
│  - Modelo ML carregado em memoria                                              │
│  - Logica de enriquecimento de features                                        │
│                                                                                 │
│  Fluxo: API Gateway → NLB → EKS (inference) → DynamoDB                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Process Repository                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Nome: elo-fraud-process-{env}                                                 │
│                                                                                 │
│  Conteudo:                                                                      │
│  - SQS consumer (polling)                                                       │
│  - Logica de processamento de feedback                                         │
│  - Escrita em DynamoDB e S3                                                    │
│                                                                                 │
│  Fluxo: SQS → EKS (process) → DynamoDB/S3                                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Model Repository                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Nome: elo-fraud-model-{env}                                                   │
│                                                                                 │
│  Conteudo:                                                                      │
│  - Container customizado para SageMaker                                        │
│  - Dependencias de ML (scikit-learn, xgboost, etc.)                           │
│  - Scripts de treinamento                                                       │
│                                                                                 │
│  Uso: SageMaker Training Jobs / Processing Jobs                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

### Servicos Kubernetes (EKS)

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `inference` | `aws_ecr_repository` | Repositorio para servico inference |
| `process` | `aws_ecr_repository` | Repositorio para servico process |
| `model` | `aws_ecr_repository` | Repositorio para container ML |
| `inference_lifecycle` | `aws_ecr_lifecycle_policy` | Lifecycle policy do inference |
| `process_lifecycle` | `aws_ecr_lifecycle_policy` | Lifecycle policy do process |
| `model_lifecycle` | `aws_ecr_lifecycle_policy` | Lifecycle policy do model |
| `inference_policy` | `aws_ecr_repository_policy` | Policy cross-account (opcional) |
| `process_policy` | `aws_ecr_repository_policy` | Policy cross-account (opcional) |
| `model_policy` | `aws_ecr_repository_policy` | Policy cross-account (opcional) |

### Lambdas (Container Image)

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `best_model_register` | `aws_ecr_repository` | Repositorio para Lambda best-model-register |
| `etl_delta_filter` | `aws_ecr_repository` | Repositorio para Lambda etl-delta-filter |
| `best_model_register_lifecycle` | `aws_ecr_lifecycle_policy` | Lifecycle policy do best-model-register |
| `etl_delta_filter_lifecycle` | `aws_ecr_lifecycle_policy` | Lifecycle policy do etl-delta-filter |

### Features por Repositorio

| Feature | Descricao | Configuravel |
|---------|-----------|--------------|
| **Image Scanning** | Scan automatico de CVEs no push | Sim |
| **Tag Mutability** | MUTABLE ou IMMUTABLE | Sim |
| **Encryption** | AES256 ou KMS customizado | Sim |
| **Lifecycle Policy** | Limpeza automatica de imagens | Sim |
| **Repository Policy** | Acesso cross-account | Sim |

---

## Lifecycle Policies

Cada repositorio possui lifecycle policies para gerenciamento automatico de imagens:

### Regras Configuradas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Lifecycle Policy Rules                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Regra 1: Imagens sem tag (Priority: 1)                                        │
│  ─────────────────────────────────────                                         │
│  Condicao: tagStatus = "untagged"                                              │
│  Tempo: 7 dias apos push                                                        │
│  Acao: Expirar                                                                  │
│                                                                                 │
│  Proposito: Remover imagens intermediarias de build                            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Regra 2: Excesso de imagens (Priority: 2)                                     │
│  ─────────────────────────────────────────                                     │
│  Condicao: imageCountMoreThan = 30                                             │
│  Acao: Expirar as mais antigas                                                  │
│                                                                                 │
│  Proposito: Manter historico para rollback, controlar custos                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Limpeza

```
Dia 0: Push da imagem v1.0.0
Dia 1: Push da imagem v1.0.1 (v1.0.0 perde tag "latest")
Dia 7: Imagem sem tag (v1.0.0) e deletada automaticamente

Dia 30+: Quando count > 30, imagens mais antigas sao deletadas
```

---

## Scan de Vulnerabilidades

O scan automatico e executado em cada push de imagem.

### Niveis de Severidade

| Severidade | Descricao | Acao Recomendada | SLA |
|------------|-----------|------------------|-----|
| **CRITICAL** | Vulnerabilidade exploravel remotamente | Bloquear deploy | Imediato |
| **HIGH** | Alto impacto na seguranca | Avaliar e corrigir | 7 dias |
| **MEDIUM** | Impacto moderado | Planejar correcao | 30 dias |
| **LOW** | Baixo impacto | Documentar | Proximo ciclo |
| **INFORMATIONAL** | Apenas informativo | Monitorar | - |

### Verificar Resultados do Scan

```bash
# Listar findings de uma imagem
aws ecr describe-image-scan-findings \
  --repository-name elo-fraud-inference-staging \
  --image-id imageTag=latest \
  --region sa-east-1

# Resumo por severidade
aws ecr describe-image-scan-findings \
  --repository-name elo-fraud-inference-staging \
  --image-id imageTag=latest \
  --query 'imageScanFindings.findingSeverityCounts' \
  --region sa-east-1
```

---

## Cross-Account Access

Permite que outras contas AWS facam pull das imagens (util para CI/CD centralizado).

### Permissoes Concedidas

```json
{
  "Action": [
    "ecr:GetDownloadUrlForLayer",
    "ecr:BatchGetImage",
    "ecr:BatchCheckLayerAvailability"
  ]
}
```

### Configuracao

```hcl
module "ecr" {
  source = "../../modules/ecr"

  # ... outras variaveis ...

  enable_cross_account_access = true
  cross_account_ids = [
    "111111111111",  # Conta de CI/CD
    "222222222222"   # Conta de producao
  ]
}
```

---

## Uso

### Uso Basico

```hcl
module "ecr" {
  source = "../../modules/ecr"

  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes dos repositorios (obrigatorios)
  inference_repo_name = "elo-fraud-inference-dev"
  process_repo_name   = "elo-fraud-process-dev"
  model_repo_name     = "elo-fraud-model-dev"
}
```

### Uso com Configuracoes Customizadas

```hcl
module "ecr" {
  source = "../../modules/ecr"

  project_name = "elo-fraud"
  environment  = "staging"

  # Nomes dos repositorios EKS (obrigatorios)
  inference_repo_name = "elo-fraud-inference-staging"
  process_repo_name   = "elo-fraud-process-staging"
  model_repo_name     = "elo-fraud-model-staging"

  # Repositorios para Lambdas (Container Image)
  best_model_register_repo_name   = "best-model-register-staging"
  create_best_model_register_repo = true

  etl_delta_filter_repo_name   = "etl-delta-filter-staging"
  create_etl_delta_filter_repo = true

  # Scan de vulnerabilidades
  enable_image_scanning = true

  # Tag mutability
  image_tag_mutability = "MUTABLE"  # ou "IMMUTABLE" para producao

  # Lifecycle
  max_image_count               = 50
  untagged_image_retention_days = 14

  tags = {
    Project     = "elo-fraud"
    Environment = "staging"
  }
}
```

### Uso Completo (Producao)

```hcl
module "ecr" {
  source = "../../modules/ecr"

  project_name = "elo-fraud"
  environment  = "prod"

  # Nomes dos repositorios (obrigatorios)
  inference_repo_name = "elo-fraud-inference-prod"
  process_repo_name   = "elo-fraud-process-prod"
  model_repo_name     = "elo-fraud-model-prod"

  # Repositorios a criar
  create_inference_repo = true
  create_process_repo   = true
  create_model_repo     = true

  # Seguranca
  enable_image_scanning = true
  image_tag_mutability  = "IMMUTABLE"  # Tags imutaveis em prod
  encryption_type       = "KMS"
  kms_key_arn          = module.kms.key_arn

  # Lifecycle policies
  max_image_count               = 100   # Mais historico em prod
  untagged_image_retention_days = 3     # Limpeza mais agressiva

  # Cross-account access
  enable_cross_account_access = true
  cross_account_ids = [
    "888577064416"  # Conta de desenvolvimento
  ]

  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    ManagedBy   = "terraform"
    Compliance  = "PCI-DSS"
  }
}
```

### Uso Seletivo (Apenas Alguns Repositorios)

```hcl
module "ecr" {
  source = "../../modules/ecr"

  project_name = "elo-fraud"
  environment  = "dev"

  # Nomes dos repositorios (obrigatorios mesmo quando create_*_repo = false)
  inference_repo_name = "elo-fraud-inference-dev"
  process_repo_name   = "elo-fraud-process-dev"
  model_repo_name     = "elo-fraud-model-dev"

  # Criar apenas repositorio de inference
  create_inference_repo = true
  create_process_repo   = false
  create_model_repo     = false
}
```

---

## Variaveis

### Obrigatorias

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `project_name` | `string` | Nome do projeto |
| `environment` | `string` | Ambiente (dev, staging, prod) |
| `inference_repo_name` | `string` | Nome do repositorio ECR para servico inference |
| `process_repo_name` | `string` | Nome do repositorio ECR para servico process |
| `model_repo_name` | `string` | Nome do repositorio ECR para container ML |

### Repositorios EKS

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `create_inference_repo` | `bool` | `true` | Criar repositorio inference |
| `create_process_repo` | `bool` | `true` | Criar repositorio process |
| `create_model_repo` | `bool` | `true` | Criar repositorio model |

### Repositorios Lambda

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `best_model_register_repo_name` | `string` | `""` | Nome do repositorio para Lambda best-model-register |
| `create_best_model_register_repo` | `bool` | `false` | Criar repositorio best-model-register |
| `etl_delta_filter_repo_name` | `string` | `""` | Nome do repositorio para Lambda etl-delta-filter |
| `create_etl_delta_filter_repo` | `bool` | `false` | Criar repositorio etl-delta-filter |

### Seguranca

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `enable_image_scanning` | `bool` | `true` | Scan automatico de CVEs |
| `image_tag_mutability` | `string` | `MUTABLE` | MUTABLE ou IMMUTABLE |
| `encryption_type` | `string` | `AES256` | AES256 ou KMS |
| `kms_key_arn` | `string` | `null` | ARN da KMS key (se KMS) |

### Lifecycle

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `max_image_count` | `number` | `30` | Maximo de imagens a manter |
| `untagged_image_retention_days` | `number` | `7` | Dias para manter imagens sem tag |

### Cross-Account

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `enable_cross_account_access` | `bool` | `false` | Habilitar acesso cross-account |
| `cross_account_ids` | `list(string)` | `[]` | Lista de Account IDs |

### Tags

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `tags` | `map(string)` | `{}` | Tags adicionais |

---

## Outputs

### Repositorios EKS

| Output | Tipo | Descricao |
|--------|------|-----------|
| `inference_repository_name` | `string` | Nome do repo inference |
| `inference_repository_url` | `string` | URL do repo inference |
| `inference_repository_arn` | `string` | ARN do repo inference |
| `process_repository_name` | `string` | Nome do repo process |
| `process_repository_url` | `string` | URL do repo process |
| `process_repository_arn` | `string` | ARN do repo process |
| `model_repository_name` | `string` | Nome do repo model |
| `model_repository_url` | `string` | URL do repo model |
| `model_repository_arn` | `string` | ARN do repo model |

### Repositorios Lambda

| Output | Tipo | Descricao |
|--------|------|-----------|
| `best_model_register_repository_name` | `string` | Nome do repo best-model-register |
| `best_model_register_repository_url` | `string` | URL do repo best-model-register |
| `best_model_register_repository_arn` | `string` | ARN do repo best-model-register |
| `etl_delta_filter_repository_name` | `string` | Nome do repo etl-delta-filter |
| `etl_delta_filter_repository_url` | `string` | URL do repo etl-delta-filter |
| `etl_delta_filter_repository_arn` | `string` | ARN do repo etl-delta-filter |

### Agregados

| Output | Tipo | Descricao |
|--------|------|-----------|
| `all_repository_arns` | `list(string)` | Lista de ARNs (para IAM policies) |
| `ecr_summary` | `object` | Resumo completo da configuracao |

### Exemplo de Uso dos Outputs

```hcl
# Em manifests Kubernetes
resource "kubernetes_deployment" "inference" {
  spec {
    template {
      spec {
        container {
          image = "${module.ecr.inference_repository_url}:latest"
        }
      }
    }
  }
}

# Em IAM policy
resource "aws_iam_policy" "ecr_pull" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
        Resource = module.ecr.all_repository_arns
      }
    ]
  })
}
```

---

## Operacoes

### Login no ECR

```bash
# Login via AWS CLI
aws ecr get-login-password --region sa-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com
```

### Build e Push de Imagem

```bash
# Build
docker build -t elo-fraud-inference-staging .

# Tag
docker tag elo-fraud-inference-staging:latest \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-inference-staging:latest

# Push
docker push \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-inference-staging:latest
```

### Listar Imagens

```bash
aws ecr list-images \
  --repository-name elo-fraud-inference-staging \
  --region sa-east-1
```

### Descrever Imagem

```bash
aws ecr describe-images \
  --repository-name elo-fraud-inference-staging \
  --image-ids imageTag=latest \
  --region sa-east-1
```

### Deletar Imagem Especifica

```bash
aws ecr batch-delete-image \
  --repository-name elo-fraud-inference-staging \
  --image-ids imageTag=v1.0.0 \
  --region sa-east-1
```

### Ver Lifecycle Policy

```bash
aws ecr get-lifecycle-policy \
  --repository-name elo-fraud-inference-staging \
  --region sa-east-1
```

### Testar Lifecycle Policy (Dry-run)

```bash
aws ecr get-lifecycle-policy-preview \
  --repository-name elo-fraud-inference-staging \
  --region sa-east-1
```

---

## Troubleshooting

### Erro: Login Failed

**Sintoma**:
```
Error: Cannot perform an interactive login from a non TTY device
```

**Solucao**: Usar pipe corretamente:
```bash
aws ecr get-login-password --region sa-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com
```

---

### Erro: Push Denied

**Sintoma**:
```
denied: Your authorization token has expired. Reauthenticate and try again.
```

**Causa**: Token expirado (valido por 12 horas).

**Solucao**: Fazer login novamente:
```bash
aws ecr get-login-password --region sa-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com
```

---

### Erro: Repository Not Found

**Sintoma**:
```
name unknown: The repository with name 'xxx' does not exist
```

**Causa**: Repositorio nao existe ou nome incorreto.

**Solucao**: Verificar repositorios existentes:
```bash
aws ecr describe-repositories --region sa-east-1
```

---

### Erro: Image Tag Already Exists (IMMUTABLE)

**Sintoma**:
```
error: tag invalid: The image tag 'v1.0.0' already exists in the 'xxx' repository and cannot be overwritten because the repository is immutable.
```

**Causa**: Tentativa de sobrescrever tag em repositorio IMMUTABLE.

**Solucao**: Usar nova tag ou mudar para MUTABLE (nao recomendado em prod):
```bash
# Usar nova tag
docker tag myimage:latest \
  888577064416.dkr.ecr.sa-east-1.amazonaws.com/repo:v1.0.1
```

---

### Verificar Configuracao do Repositorio

```bash
# Descrever repositorio
aws ecr describe-repositories \
  --repository-names elo-fraud-inference-staging \
  --region sa-east-1

# Ver encryption
aws ecr describe-repositories \
  --repository-names elo-fraud-inference-staging \
  --query 'repositories[0].encryptionConfiguration' \
  --region sa-east-1

# Ver image scanning config
aws ecr describe-repositories \
  --repository-names elo-fraud-inference-staging \
  --query 'repositories[0].imageScanningConfiguration' \
  --region sa-east-1
```

---

### Monitorar Tamanho do Repositorio

```bash
# Ver tamanho total das imagens
aws ecr describe-images \
  --repository-name elo-fraud-inference-staging \
  --query 'imageDetails[*].[imageTags[0],imageSizeInBytes]' \
  --output table \
  --region sa-east-1
```

---

## Custos Estimados

### Precos ECR (sa-east-1)

| Componente | Preco | Nota |
|------------|-------|------|
| **Storage** | $0.10 / GB / mes | Imagens armazenadas |
| **Data Transfer (Out)** | $0.09 / GB | Para fora da AWS |
| **Data Transfer (In)** | Gratuito | Upload de imagens |
| **Data Transfer (Same Region)** | Gratuito | Pull para EKS/Lambda |

### Estimativa Mensal por Ambiente

| Ambiente | Repositorios | Imagens/Repo | Tamanho Medio | Custo Estimado |
|----------|--------------|--------------|---------------|----------------|
| **DEV** | 5 | 10 | 500 MB | ~$2.50 |
| **STAGING** | 5 | 20 | 500 MB | ~$5.00 |
| **PROD** | 5 | 30 | 500 MB | ~$7.50 |

> Nota: 5 repositorios = 3 para EKS (inference, process, model) + 2 para Lambdas (best-model-register, etl-delta-filter)

### Fatores que Afetam Custo

| Fator | Impacto | Mitigacao |
|-------|---------|-----------|
| **Imagens grandes** | +Storage | Multi-stage builds, Alpine base |
| **Muitas tags** | +Storage | Lifecycle policy agressiva |
| **Sem lifecycle** | +Storage acumulado | Configurar max_image_count |
| **Pull cross-region** | +Data Transfer | Replicar para regiao local |

### Boas Praticas de Economia

| Pratica | Economia |
|---------|----------|
| Lifecycle com max 30 imagens | ~50% em storage |
| Remover untagged em 7 dias | ~10% em storage |
| Base images compartilhadas | ~30% em storage |
| Multi-stage Docker builds | ~40% em tamanho |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Repositorios separados por servico** | Permite lifecycle e permissoes independentes |
| **Tag MUTABLE em dev** | Facilita iteracao rapida com tags como `latest` |
| **Tag IMMUTABLE em prod** | Garante reproducibilidade e auditoria |
| **Scan habilitado por padrao** | Garante visibilidade de vulnerabilidades desde o inicio |
| **Lifecycle de 30 imagens** | Balanceia historico para rollback e custo de armazenamento |
| **Criptografia AES256 padrao** | Suficiente para maioria dos casos, KMS disponivel para compliance |
| **Untagged retention de 7 dias** | Remove imagens de build intermediarias rapidamente |

---

## Referencias

- [Amazon ECR User Guide](https://docs.aws.amazon.com/AmazonECR/latest/userguide/)
- [ECR Lifecycle Policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html)
- [ECR Image Scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)
- [ECR Cross-Account Access](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policy-examples.html)
