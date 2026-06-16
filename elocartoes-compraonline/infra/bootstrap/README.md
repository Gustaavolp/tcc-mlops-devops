# Bootstrap - Gerenciamento de Estado Terraform

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Provisionados](#recursos-provisionados)
- [Pre-requisitos](#pre-requisitos)
- [Guia de Implantacao](#guia-de-implantacao)
- [Configuracao do Backend](#configuracao-do-backend)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Seguranca](#seguranca)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

O **Bootstrap** e a stack responsavel por provisionar a infraestrutura de gerenciamento de estado do Terraform. Esta e a **primeira stack** que deve ser aplicada antes de qualquer outra infraestrutura do projeto.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **State Storage** | Armazenamento centralizado dos arquivos de estado Terraform |
| **State Locking** | Prevencao de execucoes simultaneas que possam corromper o estado |
| **Versionamento** | Historico de versoes para recuperacao em caso de problemas |
| **Criptografia** | Protecao dos dados sensiveis contidos no estado |

### Decisao Arquitetural

Este bootstrap utiliza uma abordagem **centralizada** - um unico bucket S3 armazena os estados de todos os ambientes (dev, staging, prod). Os estados sao organizados por prefixos no S3.

**Justificativas:**

| Aspecto | Beneficio |
|---------|-----------|
| Simplicidade | Gerenciamento de um unico bucket |
| Consistencia | Padrao uniforme de nomenclatura |
| Custo | Reducao de custos operacionais |
| Auditoria | Logs e monitoramento centralizados |
| Governanca | Politicas de acesso em um unico local |

---

## Arquitetura

```
                    AWS Account: 888577064416
                    Region: us-east-1 (Centralizado)
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   S3 Bucket: elo-fraud-terraform-state-{account}-{region}   │
    │                                                             │
    │   ┌─────────────────────────────────────────────────────┐   │
    │   │  Configuracoes:                                     │   │
    │   │  - Versionamento: Habilitado                        │   │
    │   │  - Criptografia: AES256 (SSE-S3)                    │   │
    │   │  - Locking: S3 Native (use_lockfile = true)         │   │
    │   │  - Lifecycle: prevent_destroy = true                │   │
    │   └─────────────────────────────────────────────────────┘   │
    │                                                             │
    │   Estrutura de Estados:                                     │
    │   │                                                         │
    │   ├── dev/                                                  │
    │   │   ├── foundation/terraform.tfstate                      │
    │   │   ├── mlops/terraform.tfstate                           │
    │   │   ├── platform/terraform.tfstate                        │
    │   │   ├── platform-k8s/terraform.tfstate                    │
    │   │   └── platform-lambdas/terraform.tfstate                │
    │   │                                                         │
    │   ├── staging/                                              │
    │   │   ├── foundation/terraform.tfstate                      │
    │   │   ├── mlops/terraform.tfstate                           │
    │   │   ├── platform/terraform.tfstate                        │
    │   │   ├── platform-k8s/terraform.tfstate                    │
    │   │   └── platform-lambdas/terraform.tfstate                │
    │   │                                                         │
    │   └── prod/                                                 │
    │       └── (mesma estrutura)                                 │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```

### Separacao de Responsabilidades

| Componente | Responsabilidade | Localizacao |
|------------|------------------|-------------|
| **Bootstrap** | Bucket S3 para estados | `us-east-1` (fixo) |
| **Foundation** | VPC, Subnets, Security Groups | Regiao do ambiente |
| **Platform** | EKS, API GW, DynamoDB, SQS, etc. | Regiao do ambiente |
| **Platform-K8s** | Recursos Kubernetes (Helm, KEDA, HPA) | Regiao do ambiente |
| **Platform-Lambdas** | Funcoes Lambda (register-best-model, etl-delta-filter, training-launcher) | Regiao do ambiente |
| **MLOps** | SageMaker Studio, MLflow | Regiao do ambiente |

> **Nota:** Apenas o estado Terraform e centralizado. Os recursos de infraestrutura sao provisionados nas regioes especificas de cada ambiente.

---

## Recursos Provisionados

### S3 Bucket

| Atributo | Valor |
|----------|-------|
| **Nome** | `elo-fraud-terraform-state-{account_id}-{region}` |
| **Regiao** | `us-east-1` |
| **Versionamento** | Habilitado |
| **Criptografia** | AES256 (SSE-S3) via padrao AWS (aplicada automaticamente em todos os buckets) |
| **Protecao** | `prevent_destroy = true` |

### State Locking

| Metodo | Descricao |
|--------|-----------|
| **S3 Native Locking** | Utiliza `use_lockfile = true` (Terraform 1.14+) |

> **Historico:** Ate 2026-01-20, o locking era feito via DynamoDB. A migracao para S3 native locking simplificou a arquitetura e reduziu custos.

---

## Pre-requisitos

### Versoes Requeridas

| Ferramenta | Versao Minima | Recomendada |
|------------|---------------|-------------|
| Terraform | ~> 1.14.0 | 1.14.4+ |
| AWS Provider | ~> 6.0 | Ultima estavel |
| AWS CLI | v2.x | Ultima estavel |

### Permissoes AWS Necessarias

O usuario/role que executara o bootstrap precisa das seguintes permissoes:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketVersioning",
        "s3:PutBucketEncryption",
        "s3:GetBucketVersioning",
        "s3:GetBucketEncryption",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::elo-fraud-terraform-state-*",
        "arn:aws:s3:::elo-fraud-terraform-state-*/*"
      ]
    }
  ]
}
```

### Configuracao de Credenciais

```bash
# Opcao 1: AWS CLI configurado
aws configure

# Opcao 2: Variaveis de ambiente
export AWS_ACCESS_KEY_ID="sua-access-key"
export AWS_SECRET_ACCESS_KEY="sua-secret-key"
export AWS_REGION="us-east-1"

# Opcao 3: AWS SSO
aws sso login --profile seu-perfil
export AWS_PROFILE=seu-perfil
```

---

## Guia de Implantacao

### Primeira Execucao (Novo Ambiente)

```bash
# 1. Navegue ate o diretorio do bootstrap
cd infra/bootstrap

# 2. Confirme o state_bucket_name no terraform.tfvars
# Formato: elo-fraud-terraform-state-{account_id}-{region}
# O arquivo ja existe preenchido com os valores do projeto:
cat terraform.tfvars

# 3. Inicialize o Terraform
terraform init

# 4. Visualize as mudancas planejadas
terraform plan

# 5. Aplique as mudancas
terraform apply

# 6. Anote os outputs para uso nas outras stacks
terraform output
```

### Verificacao Pos-Implantacao

```bash
# Verificar se o bucket foi criado
aws s3 ls | grep elo-fraud-terraform-state

# Verificar configuracoes do bucket
aws s3api get-bucket-versioning --bucket elo-fraud-terraform-state-888577064416-us-east-1
aws s3api get-bucket-encryption --bucket elo-fraud-terraform-state-888577064416-us-east-1

# Ver outputs da stack
terraform output
```

---

## Configuracao do Backend

Apos aplicar o bootstrap, utilize esta configuracao nas demais stacks:

### Template Generico

```hcl
terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "ENVIRONMENT/STACK_NAME/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true  # S3 native locking (Terraform 1.14+)
  }
}
```

### Exemplos por Stack

| Ambiente | Stack | Key |
|----------|-------|-----|
| dev | foundation | `dev/foundation/terraform.tfstate` |
| dev | platform | `dev/platform/terraform.tfstate` |
| dev | platform-k8s | `dev/platform-k8s/terraform.tfstate` |
| dev | platform-lambdas | `dev/platform-lambdas/terraform.tfstate` |
| dev | mlops | `dev/mlops/terraform.tfstate` |
| staging | foundation | `staging/foundation/terraform.tfstate` |
| staging | mlops | `staging/mlops/terraform.tfstate` |
| staging | platform | `staging/platform/terraform.tfstate` |
| staging | platform-k8s | `staging/platform-k8s/terraform.tfstate` |
| staging | platform-lambdas | `staging/platform-lambdas/terraform.tfstate` |
| prod | foundation | `prod/foundation/terraform.tfstate` |

---

## Estrutura de Arquivos

```
infra/bootstrap/
├── main.tf              # Recursos principais (S3 bucket + versionamento)
├── variables.tf         # Definicao de variaveis
├── outputs.tf           # Outputs exportados
├── terraform.tfvars     # Valores configurados para o projeto
└── README.md            # Esta documentacao
```

### Descricao dos Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `main.tf` | Define o bucket S3 com versionamento e lifecycle prevent_destroy |
| `variables.tf` | Variaveis configuraveis (aws_region, state_bucket_name, tags) |
| `outputs.tf` | Exporta nome do bucket, ARN e regiao |
| `terraform.tfvars` | Valores do projeto (bucket name, regiao, tags) |

---

## Variaveis

| Variavel | Tipo | Obrigatorio | Descricao |
|----------|------|-------------|-----------|
| `aws_region` | string | Nao (padrao: `us-east-1`) | Regiao AWS onde o bucket sera criado (centralizado para todos os states) |
| `state_bucket_name` | string | **Sim** | Nome do bucket S3 para Terraform state. Formato recomendado: `{project}-terraform-state-{account_id}-{region}` |
| `tags` | map(string) | Nao (padrao fornecido) | Tags comuns aplicadas aos recursos. Default serve como template organizacional |

### Tags Padrao

```hcl
tags = {
  Project   = "Elo Fraud Detection"
  ManagedBy = "Terraform"
  Owner     = "DevOps"
  Purpose   = "Terraform State Management"
}
```

---

## Outputs

| Output | Descricao | Exemplo |
|--------|-----------|---------|
| `terraform_state_bucket_name` | Nome do bucket S3 | `elo-fraud-terraform-state-888577064416-us-east-1` |
| `terraform_state_bucket_arn` | ARN do bucket S3 | `arn:aws:s3:::elo-fraud-terraform-state-888577064416-us-east-1` |
| `terraform_state_bucket_region` | Regiao do bucket | `us-east-1` |

---

## Seguranca

### Controles Implementados

| Controle | Descricao |
|----------|-----------|
| **Criptografia em Repouso** | AES256 (SSE-S3) aplicada automaticamente pelo AWS (padrao desde 2023) |
| **Versionamento** | Permite recuperacao de estados anteriores |
| **Prevent Destroy** | Lifecycle rule que impede exclusao acidental |
| **State Locking** | Previne execucoes simultaneas |

### Recomendacoes Adicionais

1. **Bucket Policy**: Considere adicionar uma bucket policy restritiva
2. **Access Logs**: Habilite S3 access logs para auditoria
3. **MFA Delete**: Considere habilitar para ambientes produtivos
4. **Cross-Region Replication**: Para disaster recovery em producao

### Exemplo de Bucket Policy Restritiva

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::elo-fraud-terraform-state-*/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    },
    {
      "Sid": "DenyInsecureConnections",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::elo-fraud-terraform-state-*",
        "arn:aws:s3:::elo-fraud-terraform-state-*/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

---

## Operacoes

### Visualizar Estados Armazenados

```bash
# Listar todos os estados
aws s3 ls s3://elo-fraud-terraform-state-888577064416-us-east-1/ --recursive

# Listar estados de um ambiente especifico
aws s3 ls s3://elo-fraud-terraform-state-888577064416-us-east-1/dev/
```

### Backup de Estado

```bash
# Backup de um estado especifico
aws s3 cp \
  s3://elo-fraud-terraform-state-888577064416-us-east-1/dev/platform/terraform.tfstate \
  ./backup-terraform.tfstate

# Backup de todos os estados
aws s3 sync \
  s3://elo-fraud-terraform-state-888577064416-us-east-1/ \
  ./backup-states/
```

### Recuperar Versao Anterior

```bash
# Listar versoes de um estado
aws s3api list-object-versions \
  --bucket elo-fraud-terraform-state-888577064416-us-east-1 \
  --prefix dev/platform/terraform.tfstate

# Restaurar versao especifica
aws s3api get-object \
  --bucket elo-fraud-terraform-state-888577064416-us-east-1 \
  --key dev/platform/terraform.tfstate \
  --version-id "VERSION_ID" \
  ./restored-terraform.tfstate
```

### Migracao de Estado

```bash
# Copiar estado de um bucket para outro
aws s3 cp \
  s3://bucket-origem/path/terraform.tfstate \
  s3://bucket-destino/path/terraform.tfstate

# Apos copiar, atualize o backend.tf e execute:
terraform init -reconfigure
```

---

## Troubleshooting

### Erro: State Lock

**Sintoma:**
```
Error: Error acquiring the state lock
```

**Causa:** Outra execucao do Terraform esta em andamento ou travou.

**Solucao:**
```bash
# Verificar se ha execucoes em andamento
# Se nao houver, force o unlock:
terraform force-unlock LOCK_ID
```

### Erro: Bucket Already Exists

**Sintoma:**
```
Error: Error creating S3 bucket: BucketAlreadyOwnedByYou
```

**Causa:** O bucket ja existe.

**Solucao:**
```bash
# Importe o recurso existente
terraform import aws_s3_bucket.terraform_state BUCKET_NAME
```

### Erro: Access Denied

**Sintoma:**
```
Error: Access Denied when accessing S3 bucket
```

**Causa:** Permissoes insuficientes.

**Solucao:**
1. Verifique as credenciais AWS configuradas
2. Confirme que o usuario/role tem as permissoes listadas nos pre-requisitos
3. Verifique se ha SCPs (Service Control Policies) bloqueando acoes

### Erro: Invalid use_lockfile

**Sintoma:**
```
Error: Invalid backend configuration argument
```

**Causa:** Versao do Terraform anterior a 1.14.

**Solucao:**
```bash
# Atualize o Terraform para versao 1.14+
tfenv install 1.14.4
tfenv use 1.14.4
```

