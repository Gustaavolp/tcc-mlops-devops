# Foundation Stack - DEV

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

A **Foundation Stack** provisiona a infraestrutura base compartilhada do ambiente DEV. Esta e a **primeira stack do ambiente** que deve ser aplicada apos o bootstrap, pois fornece os recursos de rede e armazenamento consumidos pelas demais stacks.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Networking** | VPC, Subnets, Internet Gateway, NAT Gateway, VPC Endpoints |
| **Storage** | Buckets S3 para dados, modelos, logs e recursos |
| **Security Groups** | Grupos de seguranca para ALB e VPC Endpoints |
| **Conectividade** | Acesso privado a servicos AWS sem internet publica |

### Por que uma Stack Separada?

| Beneficio | Descricao |
|-----------|-----------|
| **Isolamento** | Mudancas em outras stacks nao afetam a rede |
| **Performance** | Deploy mais rapido das stacks dependentes |
| **Seguranca** | Controle de acesso diferenciado (apenas admins alteram Foundation) |
| **Estabilidade** | Recursos raramente mudam apos configuracao inicial |

---

## Arquitetura

```
                            AWS Region: us-east-1
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   VPC: 10.0.0.0/16                                                          │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Availability Zone: us-east-1a                   │   │
│   │                                                                     │   │
│   │   ┌─────────────────────┐    ┌─────────────────────┐               │   │
│   │   │  Public Subnet      │    │  Private Subnet     │               │   │
│   │   │  10.0.1.0/24        │    │  10.0.11.0/24       │               │   │
│   │   │                     │    │                     │               │   │
│   │   │  - NAT Gateway      │    │  - EKS Nodes        │               │   │
│   │   │  - ALB (se externo) │    │  - ALB (interno)    │               │   │
│   │   └─────────────────────┘    └─────────────────────┘               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Availability Zone: us-east-1b                   │   │
│   │                                                                     │   │
│   │   ┌─────────────────────┐    ┌─────────────────────┐               │   │
│   │   │  Public Subnet      │    │  Private Subnet     │               │   │
│   │   │  10.0.2.0/24        │    │  10.0.12.0/24       │               │   │
│   │   │                     │    │                     │               │   │
│   │   └─────────────────────┘    └─────────────────────┘               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        VPC Endpoints                                │   │
│   │                                                                     │   │
│   │   Gateway (Gratuitos):        Interface (~$7.20/endpoint/AZ):       │   │
│   │   - S3                        - ECR API          - SageMaker API    │   │
│   │   - DynamoDB                  - ECR DKR          - SageMaker Runtime│   │
│   │                               - CloudWatch Logs  - Kinesis Firehose │   │
│   │                               - SQS              - EC2              │   │
│   │                               - STS                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                          Internet Gateway                           │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│                              S3 Buckets                                     │
│                                                                             │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│   │     raw       │  │   processed   │  │    models     │                  │
│   │  Dados brutos │  │ Bronze/Silver │  │  Artefatos ML │                  │
│   │    3DS/TE40   │  │     Gold      │  │   treinados   │                  │
│   └───────────────┘  └───────────────┘  └───────────────┘                  │
│                                                                             │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│   │     logs      │  │   resources   │  │reports-promo  │                  │
│   │Logs centrali- │  │  Templates,   │  │   Relatorios  │                  │
│   │    zados      │  │   configs     │  │   promocao    │                  │
│   └───────────────┘  └───────────────┘  └───────────────┘                  │
│                                                                             │
│   ┌───────────────┐                                                        │
│   │reports-stats  │                                                        │
│   │  Estatisticas │                                                        │
│   └───────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Conectividade

```
Internet
    │
    ▼
┌─────────────────┐
│ Internet Gateway│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Public Subnet  │────▶│  NAT Gateway    │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Private Subnet  │
                        │                 │
                        │  - EKS Nodes    │◀──── VPC Endpoints ────▶ AWS Services
                        │  - ALB interno  │      (sem internet)
                        └─────────────────┘
```

---

## Recursos Provisionados

### VPC e Networking

| Recurso | Configuracao | Descricao |
|---------|--------------|-----------|
| **VPC** | 10.0.0.0/16 | Rede isolada com 65.536 IPs disponiveis |
| **Public Subnets** | 10.0.1.0/24, 10.0.2.0/24 | Para recursos com acesso publico (NAT GW) |
| **Private Subnets** | 10.0.11.0/24, 10.0.12.0/24 | Para recursos internos (EKS, ALB) |
| **Internet Gateway** | 1 | Acesso de/para internet para subnets publicas |
| **NAT Gateway** | 1 (single) | Acesso de saida para subnets privadas |
| **Route Tables** | 2 | Publica e privada com rotas configuradas |

### VPC Endpoints

#### Gateway Endpoints (Gratuitos)

| Endpoint | Servico | Uso |
|----------|---------|-----|
| **S3** | com.amazonaws.us-east-1.s3 | Acesso a buckets S3 |
| **DynamoDB** | com.amazonaws.us-east-1.dynamodb | Acesso a tabelas DynamoDB |

#### Interface Endpoints (Pagos)

| Endpoint | Servico | Uso |
|----------|---------|-----|
| **ECR API** | com.amazonaws.us-east-1.ecr.api | Autenticacao ECR |
| **ECR DKR** | com.amazonaws.us-east-1.ecr.dkr | Pull de imagens Docker |
| **CloudWatch Logs** | com.amazonaws.us-east-1.logs | Envio de logs |
| **SQS** | com.amazonaws.us-east-1.sqs | Acesso a filas |
| **STS** | com.amazonaws.us-east-1.sts | Autenticacao IAM (EKS) |
| **EC2** | com.amazonaws.us-east-1.ec2 | VPC CNI do EKS |
| **SageMaker API** | com.amazonaws.us-east-1.sagemaker.api | Chamadas API SageMaker |
| **SageMaker Runtime** | com.amazonaws.us-east-1.sagemaker.runtime | Inferencia ML |
| **Kinesis Firehose** | com.amazonaws.us-east-1.firehose | Streaming de dados |

### Security Groups

| Security Group | Proposito | Regras Principais |
|----------------|-----------|-------------------|
| **ALB** | Application Load Balancer | Ingress do VPC CIDR (interno) |
| **VPC Endpoints** | Interface Endpoints | HTTPS (443) do VPC CIDR |

### S3 Buckets

| Bucket | Nome | Finalidade | Lifecycle |
|--------|------|------------|-----------|
| **raw** | elo-fraud-raw-dev-{account} | Dados brutos 3DS e TE40 | 30d → Glacier |
| **processed** | elo-fraud-processed-dev-{account} | Dados Bronze/Silver/Gold | 90d → Glacier |
| **models** | elo-fraud-models-dev-{account} | Artefatos ML treinados | Sem expiracao |
| **logs** | elo-fraud-logs-dev-{account} | Logs centralizados | 90d → Expiracao |
| **resources** | elo-fraud-resources-dev-{account} | Templates e configs | Versionado |
| **reports-promotion** | elo-fraud-reports-promotion-dev-{account} | Relatorios promocao | Versionado |
| **reports-statistics** | elo-fraud-reports-statistics-dev-{account} | Estatisticas | Versionado |

#### Configuracoes Comuns dos Buckets

| Configuracao | Valor |
|--------------|-------|
| **Versionamento** | Habilitado |
| **Criptografia** | AES256 (SSE-S3) |
| **Intelligent Tiering** | Habilitado |
| **Force Destroy** | true (apenas dev) |

---

## Pre-requisitos

### Dependencias

| Requisito | Descricao |
|-----------|-----------|
| **Bootstrap** | Stack de bootstrap aplicada (bucket S3 de state) |
| **Terraform** | >= 1.10.0 |
| **AWS Provider** | ~> 5.0 |
| **AWS CLI** | v2.x configurado |

### Permissoes AWS Necessarias

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "s3:*",
        "logs:*"
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
# 1. Navegue ate o diretorio
cd infra/environments/dev/foundation

# 2. Inicialize o Terraform
terraform init

# 3. Visualize as mudancas
terraform plan

# 4. Aplique a infraestrutura
terraform apply

# 5. Verifique os outputs
terraform output
```

### Verificacao Pos-Implantacao

```bash
# Verificar VPC criada
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=elo-fraud" --region us-east-1

# Verificar subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" --region us-east-1

# Verificar VPC Endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" --region us-east-1

# Listar buckets S3
aws s3 ls | grep elo-fraud
```

---

## Estrutura de Arquivos

```
infra/environments/dev/foundation/
├── main.tf              # Recursos principais (VPC, S3)
├── variables.tf         # Definicao de variaveis
├── outputs.tf           # Outputs para outras stacks
├── backend.tf           # Configuracao do backend S3
├── providers.tf         # Configuracao de providers
├── terraform.tfvars     # Valores das variaveis
└── README.md            # Esta documentacao
```

| Arquivo | Descricao |
|---------|-----------|
| `main.tf` | Instancia modulos VPC e S3, cria buckets adicionais |
| `variables.tf` | Define todas as variaveis configuraveis |
| `outputs.tf` | Exporta valores para stacks dependentes |
| `backend.tf` | Backend S3 com locking nativo |
| `providers.tf` | Provider AWS com default tags |
| `terraform.tfvars` | Valores especificos do ambiente DEV |

---

## Variaveis

### Gerais

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `project_name` | string | `elo-fraud` | Nome do projeto |
| `environment` | string | `dev` | Ambiente |
| `aws_region` | string | `us-east-1` | Regiao AWS |
| `aws_account_id` | string | `888577064416` | ID da conta AWS |

### VPC

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `vpc_cidr` | string | `10.0.0.0/16` | CIDR block da VPC |
| `availability_zones` | list(string) | `["us-east-1a", "us-east-1b"]` | AZs utilizadas |
| `public_subnet_cidrs` | list(string) | `["10.0.1.0/24", "10.0.2.0/24"]` | CIDRs publicas |
| `private_subnet_cidrs` | list(string) | `["10.0.11.0/24", "10.0.12.0/24"]` | CIDRs privadas |
| `enable_nat_gateway` | bool | `false` | Habilitar NAT Gateway (desabilitado - usa VPC Endpoints) |
| `single_nat_gateway` | bool | `true` | Usar apenas 1 NAT Gateway |
| `enable_vpc_endpoints` | bool | `true` | Habilitar Gateway Endpoints |
| `enable_interface_endpoints` | bool | `true` | Habilitar Interface Endpoints |

### S3

> **NOTA:** As configuracoes de lifecycle, versionamento e intelligent tiering sao
> gerenciadas internamente pelo modulo S3. Consulte `infra/modules/s3/README.md`
> para detalhes das configuracoes aplicadas.

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `common_tags` | map(string) | (ver variables.tf) | Tags aplicadas a todos os recursos |

---

## Outputs

### VPC

| Output | Descricao |
|--------|-----------|
| `vpc_id` | ID da VPC |
| `vpc_cidr` | CIDR block da VPC |
| `public_subnet_ids` | IDs das subnets publicas |
| `private_subnet_ids` | IDs das subnets privadas |
| `internet_gateway_id` | ID do Internet Gateway |
| `nat_gateway_ids` | IDs dos NAT Gateways |
| `nat_gateway_public_ips` | IPs publicos dos NAT Gateways |
| `security_group_alb_id` | Security Group do ALB |
| `security_group_vpc_endpoints_id` | Security Group dos VPC Endpoints |

### VPC Endpoints

| Output | Descricao |
|--------|-----------|
| `vpc_endpoint_ecr_api_id` | ID do Endpoint ECR API |
| `vpc_endpoint_ecr_dkr_id` | ID do Endpoint ECR DKR |
| `vpc_endpoint_logs_id` | ID do Endpoint CloudWatch Logs |
| `vpc_endpoint_sqs_id` | ID do Endpoint SQS |
| `vpc_endpoint_sts_id` | ID do Endpoint STS |
| `vpc_endpoint_ec2_id` | ID do Endpoint EC2 |
| `vpc_endpoint_sagemaker_api_id` | ID do Endpoint SageMaker API |
| `vpc_endpoint_sagemaker_runtime_id` | ID do Endpoint SageMaker Runtime |
| `vpc_endpoint_firehose_id` | ID do Endpoint Firehose |

### S3

| Output | Descricao |
|--------|-----------|
| `s3_raw_bucket_id` / `s3_raw_bucket_arn` | Bucket de dados brutos |
| `s3_processed_bucket_id` / `s3_processed_bucket_arn` | Bucket de dados processados |
| `s3_models_bucket_id` / `s3_models_bucket_arn` | Bucket de modelos ML |
| `s3_logs_bucket_id` / `s3_logs_bucket_arn` | Bucket de logs |
| `s3_resources_bucket_id` / `s3_resources_bucket_arn` | Bucket de recursos |
| `s3_reports_promotion_bucket_id` / `s3_reports_promotion_bucket_arn` | Bucket de relatorios promocao |
| `s3_reports_statistics_bucket_id` / `s3_reports_statistics_bucket_arn` | Bucket de estatisticas |
| `s3_all_bucket_arns` | Lista de ARNs de todos os buckets |

### Resumo

| Output | Descricao |
|--------|-----------|
| `foundation_summary` | Objeto com resumo completo da stack (environment, region, vpc, s3_buckets) |
| `usage_instructions` | Instrucoes para usar os outputs em outras stacks via remote_state |

---

## Integracao com Outras Stacks

### Como Consumir os Outputs

As stacks dependentes (MLOps, Platform, Platform-K8s) devem usar `terraform_remote_state`:

```hcl
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

# Exemplos de uso:
locals {
  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids
  models_bucket_arn  = data.terraform_remote_state.foundation.outputs.s3_models_bucket_arn
}
```

### Ordem de Implantacao

```
1. bootstrap          (state management)
       │
       ▼
2. foundation         (VPC, S3) ◀── ESTA STACK
       │
       ├──────────────────┐
       ▼                  ▼
3. mlops            platform
   (SageMaker)      (EKS, SQS, DynamoDB)
                          │
                          ▼
                    platform-k8s
                    (Helm, K8s resources)
                          │
                          ▼
                    platform-lambdas
                    (Lambda functions)
```

### Stacks Dependentes

| Stack | Recursos Consumidos |
|-------|---------------------|
| **MLOps** | VPC, subnets, S3 buckets (models, logs) |
| **Platform** | VPC, subnets, security groups, S3 buckets |
| **Platform-K8s** | VPC ID (via Platform remote state) |
| **Platform-Lambdas** | S3 buckets, VPC (opcional) |

---

## Custos Estimados

### Resumo Mensal (DEV)

| Recurso | Quantidade | Custo Unitario | Custo Total |
|---------|------------|----------------|-------------|
| **NAT Gateway** | 1 | $32.00/mes | $32.00 |
| **NAT Gateway Data** | ~10 GB | $0.045/GB | ~$0.45 |
| **Interface Endpoints** | 9 x 2 AZs | $7.20/endpoint/AZ | ~$129.60 |
| **S3 Storage** | ~50 GB | $0.023/GB | ~$1.15 |
| **S3 Requests** | Variavel | Pay-per-use | ~$1.00 |
| | | **Total Estimado** | **~$164.20** |

### Otimizacoes Aplicadas

| Otimizacao | Economia |
|------------|----------|
| Single NAT Gateway (ao inves de 1 por AZ) | ~$32/mes |
| Gateway Endpoints para S3/DynamoDB | Gratuitos (vs NAT data transfer) |
| Intelligent Tiering nos buckets | Automatico |
| Glacier transition para dados antigos | Reducao de storage |

---

## Operacoes

### Verificar Estado dos VPC Endpoints

```bash
# Status de todos os endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'VpcEndpoints[*].[ServiceName,State]' \
  --output table
```

### Verificar Conectividade Privada

```bash
# De dentro de um pod EKS ou EC2 na subnet privada
# Testar acesso ao ECR sem internet
aws ecr get-login-password --region us-east-1
```

### Limpar Buckets S3 (antes de destroy)

```bash
# Listar e esvaziar um bucket especifico
aws s3 rm s3://elo-fraud-raw-dev-888577064416 --recursive
aws s3 rm s3://elo-fraud-processed-dev-888577064416 --recursive
```

### Destruir Infraestrutura

```bash
# ATENCAO: Apenas em ambiente de desenvolvimento
# Destruir nesta ordem reversa:
# 1. platform-lambdas
# 2. platform-k8s
# 3. platform
# 4. mlops
# 5. foundation (esta stack)

terraform destroy
```

---

## Troubleshooting

### Erro: VPC Endpoint em estado "failed"

**Sintoma:**
```
VPC Endpoint state: failed
```

**Causa:** Servico nao disponivel na regiao ou problema de permissao.

**Solucao:**
```bash
# Verificar disponibilidade do servico
aws ec2 describe-vpc-endpoint-services --region us-east-1 \
  --query 'ServiceNames[?contains(@, `sagemaker`)]'

# Recriar o endpoint
terraform taint 'module.vpc.aws_vpc_endpoint.interface["sagemaker.api"]'
terraform apply
```

### Erro: Subnet CIDR conflicts

**Sintoma:**
```
Error: CIDR block 10.0.1.0/24 conflicts with existing subnet
```

**Causa:** Subnet ja existe na VPC.

**Solucao:**
```bash
# Verificar subnets existentes
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx"

# Importar se necessario
terraform import 'module.vpc.aws_subnet.public[0]' subnet-xxx
```

### Erro: S3 bucket already exists

**Sintoma:**
```
Error: Error creating S3 bucket: BucketAlreadyExists
```

**Causa:** Nome de bucket deve ser globalmente unico.

**Solucao:**
```bash
# Verificar se o bucket existe
aws s3 ls | grep elo-fraud

# Importar bucket existente
terraform import 'module.s3.aws_s3_bucket.raw' elo-fraud-raw-dev-888577064416
```

### Erro: NAT Gateway failed

**Sintoma:**
```
Error: Error creating NAT Gateway: NatGatewayLimitExceeded
```

**Causa:** Limite de NAT Gateways na conta/regiao.

**Solucao:**
1. Solicitar aumento de limite via AWS Support
2. Ou usar NAT Instance como alternativa temporaria

### Pods nao conseguem acessar ECR

**Sintoma:**
```
Error: Pull access denied or repository does not exist
```

**Causa:** VPC Endpoints de ECR nao funcionando ou Security Group bloqueando.

**Solucao:**
```bash
# Verificar status dos endpoints ECR
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=*ecr*" \
  --query 'VpcEndpoints[*].[VpcEndpointId,State,ServiceName]'

# Verificar Security Group permite 443
aws ec2 describe-security-groups --group-ids sg-xxx
```
