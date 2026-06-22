# VPC Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Subnets](#subnets)
- [VPC Endpoints](#vpc-endpoints)
- [Security Groups](#security-groups)
- [NAT Gateway vs VPC Endpoints](#nat-gateway-vs-vpc-endpoints)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)
- [Custos Estimados](#custos-estimados)
- [Decisoes de Arquitetura](#decisoes-de-arquitetura)
- [Referencias](#referencias)

---

## Visao Geral

Este modulo provisiona uma **Amazon VPC (Virtual Private Cloud)** que fornece a infraestrutura de rede isolada para todos os recursos do sistema de deteccao de fraude.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Isolamento** | Rede privada separada da internet publica |
| **Seguranca** | Security Groups e NACLs controlam todo trafego |
| **Alta Disponibilidade** | Subnets distribuidas em multiplas AZs |
| **Conectividade AWS** | VPC Endpoints para acesso privado a servicos AWS |

### Caracteristicas

| Caracteristica | Valor |
|----------------|-------|
| **Subnets** | Publicas e Privadas em multiplas AZs |
| **Gateway Endpoints** | S3, DynamoDB (gratuitos) |
| **Interface Endpoints** | ECR, SQS, STS, EC2, SageMaker, Firehose, CloudWatch |
| **NAT Gateway** | Opcional (desabilitado por padrao) |
| **Security Groups** | Pre-configurados para ALB e VPC Endpoints |

---

## Arquitetura

```
                                    AWS Region
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                     VPC                                          │
│                               (CIDR: 10.0.0.0/16)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                          INTERNET GATEWAY                                 │  │
│   └────────────────────────────────────┬─────────────────────────────────────┘  │
│                                        │                                         │
│   ┌────────────────────────────────────┼────────────────────────────────────┐   │
│   │                          PUBLIC SUBNETS                                  │   │
│   │                                                                          │   │
│   │   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐          │   │
│   │   │   AZ-a         │   │   AZ-b         │   │   AZ-c         │          │   │
│   │   │ 10.0.1.0/24    │   │ 10.0.2.0/24    │   │ 10.0.3.0/24    │          │   │
│   │   │                │   │                │   │                │          │   │
│   │   │     ALB        │   │     ALB        │   │     ALB        │          │   │
│   │   │   (NAT GW)     │   │   (NAT GW)     │   │   (NAT GW)     │          │   │
│   │   └────────────────┘   └────────────────┘   └────────────────┘          │   │
│   │                                                                          │   │
│   └────────────────────────────────────┬────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────┼────────────────────────────────────┐   │
│   │                         PRIVATE SUBNETS                                  │   │
│   │                                                                          │   │
│   │   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐          │   │
│   │   │   AZ-a         │   │   AZ-b         │   │   AZ-c         │          │   │
│   │   │ 10.0.11.0/24   │   │ 10.0.12.0/24   │   │ 10.0.13.0/24   │          │   │
│   │   │                │   │                │   │                │          │   │
│   │   │  EKS Nodes     │   │  EKS Nodes     │   │  EKS Nodes     │          │   │
│   │   │  Lambda        │   │  Lambda        │   │  Lambda        │          │   │
│   │   └────────────────┘   └────────────────┘   └────────────────┘          │   │
│   │                                                                          │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│   ┌────────────────────────────────────┼────────────────────────────────────┐   │
│   │                         VPC ENDPOINTS                                    │   │
│   │                                                                          │   │
│   │   Gateway:     S3  ─────  DynamoDB                                      │   │
│   │                                                                          │   │
│   │   Interface:   ECR API  ─  ECR DKR  ─  CloudWatch Logs  ─  SQS         │   │
│   │                STS  ─  EC2  ─  SageMaker API  ─  SageMaker Runtime     │   │
│   │                Kinesis Firehose                                         │   │
│   │                                                                          │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Trafego

```
                        TRAFEGO DE ENTRADA
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   Internet ────► IGW ────► ALB (public) ────► EKS Pods (private)                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                     TRAFEGO DE SAIDA (sem NAT Gateway)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   EKS (private) ────► VPC Endpoint ────► S3 / DynamoDB / SageMaker / ECR        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

                     TRAFEGO DE SAIDA (com NAT Gateway)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   EKS (private) ────► NAT Gateway ────► IGW ────► Internet                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_vpc.main` | VPC | Rede privada virtual |
| `aws_internet_gateway.main` | Internet Gateway | Conexao com internet |
| `aws_subnet.public` | Subnets | Subnets publicas (por AZ) |
| `aws_subnet.private` | Subnets | Subnets privadas (por AZ) |
| `aws_eip.nat` | Elastic IP | IPs para NAT Gateway (se habilitado) |
| `aws_nat_gateway.main` | NAT Gateway | Saida para internet (se habilitado) |
| `aws_route_table.public` | Route Table | Roteamento subnets publicas |
| `aws_route_table.private` | Route Table | Roteamento subnets privadas |
| `aws_security_group.alb` | Security Group | Regras para ALB |
| `aws_security_group.vpc_endpoints` | Security Group | Regras para Interface Endpoints |
| `aws_vpc_endpoint.s3` | Gateway Endpoint | Acesso privado ao S3 |
| `aws_vpc_endpoint.dynamodb` | Gateway Endpoint | Acesso privado ao DynamoDB |
| `aws_vpc_endpoint.*` | Interface Endpoints | Acesso privado a servicos AWS |

### Convencao de Nomes

```
{project_name}-{recurso}-{environment}

Exemplos:
- elo-fraud-vpc-dev
- elo-fraud-igw-staging
- elo-fraud-public-subnet-dev-us-east-1a
- elo-fraud-private-subnet-prod-us-east-1b
- elo-fraud-sg-alb-dev
- elo-fraud-vpce-s3-staging
```

---

## Subnets

### Tipos de Subnets

| Tipo | Caracteristicas | Uso |
|------|-----------------|-----|
| **Publicas** | IP publico automatico, rota para IGW | ALB, Bastion hosts, NAT Gateway |
| **Privadas** | Sem IP publico, rota para NAT/Endpoints | EKS nodes, Lambda, RDS, ElastiCache |

### Distribuicao por AZ

```
┌─────────────────────────────────────────────────────────────────┐
│                         Availability Zones                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│      AZ-a       │      AZ-b       │      AZ-c                   │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ Public:         │ Public:         │ Public:                     │
│ 10.0.1.0/24     │ 10.0.2.0/24     │ 10.0.3.0/24                │
│ (251 IPs)       │ (251 IPs)       │ (251 IPs)                  │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ Private:        │ Private:        │ Private:                    │
│ 10.0.11.0/24    │ 10.0.12.0/24    │ 10.0.13.0/24               │
│ (251 IPs)       │ (251 IPs)       │ (251 IPs)                  │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## VPC Endpoints

### Gateway Endpoints (Gratuitos)

| Endpoint | Servico | Finalidade |
|----------|---------|------------|
| **S3** | `com.amazonaws.{region}.s3` | Acesso a buckets de dados e modelos |
| **DynamoDB** | `com.amazonaws.{region}.dynamodb` | Acesso ao feature store |

### Interface Endpoints (~$7.20/mes cada por AZ)

| Endpoint | Servico | Finalidade | Obrigatorio |
|----------|---------|------------|-------------|
| **ECR API** | `ecr.api` | Autenticacao no registry | EKS |
| **ECR DKR** | `ecr.dkr` | Pull de imagens Docker | EKS |
| **CloudWatch Logs** | `logs` | Envio de logs dos pods | EKS |
| **SQS** | `sqs` | Acesso as filas de transacoes | Process Service |
| **STS** | `sts` | Autenticacao IAM dos nodes EKS | **EKS (obrigatorio)** |
| **EC2** | `ec2` | VPC CNI gerenciar ENIs | **EKS (obrigatorio)** |
| **SageMaker API** | `sagemaker.api` | Chamadas describe_endpoint | Inference Service |
| **SageMaker Runtime** | `sagemaker.runtime` | Inferencia (invoke_endpoint) | Inference Service |
| **Kinesis Firehose** | `kinesis-firehose` | Streaming de dados | Data Pipeline |

---

## Security Groups

### ALB Security Group

Configuracao dinamica baseada na variavel `alb_internal`:

**Modo Publico** (`alb_internal = false`):

| Direcao | Porta | Origem/Destino | Descricao |
|---------|-------|----------------|-----------|
| Ingress | 443 | 0.0.0.0/0 | HTTPS da internet |
| Ingress | 80 | 0.0.0.0/0 | HTTP (redirect para HTTPS) |
| Egress | All | 0.0.0.0/0 | Trafego para EKS pods |

**Modo Interno** (`alb_internal = true`):

| Direcao | Porta | Origem/Destino | Descricao |
|---------|-------|----------------|-----------|
| Ingress | 443 | VPC CIDR | HTTPS da VPC (via NLB) |
| Ingress | 80 | VPC CIDR | HTTP da VPC (via NLB) |
| Egress | All | 0.0.0.0/0 | Trafego para EKS pods |

### VPC Endpoints Security Group

| Direcao | Porta | Origem/Destino | Descricao |
|---------|-------|----------------|-----------|
| Ingress | 443 | VPC CIDR | HTTPS de dentro da VPC |

---

## NAT Gateway vs VPC Endpoints

### Comparativo

| Aspecto | NAT Gateway | VPC Endpoints |
|---------|-------------|---------------|
| **Custo fixo** | ~$32/mes por gateway | ~$7.20/mes por endpoint |
| **Custo por dados** | $0.045/GB | Gratuito (Gateway) |
| **Latencia** | Maior (via internet) | Menor (rede AWS) |
| **Seguranca** | Trafego via internet | Trafego privado |
| **Cobertura** | Qualquer servico/API | Servicos AWS especificos |

### Recomendacao

| Cenario | Recomendacao |
|---------|--------------|
| **Apenas servicos AWS** | VPC Endpoints (sem NAT) |
| **APIs externas necessarias** | NAT Gateway + VPC Endpoints |
| **Desenvolvimento** | VPC Endpoints (economia) |
| **Producao** | VPC Endpoints + NAT opcional |

---

## Uso

### Uso Basico

```hcl
module "vpc" {
  source = "../../modules/vpc"

  project_name = "elo-fraud"
  environment  = "dev"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
}
```

### Uso com VPC Endpoints

```hcl
module "vpc" {
  source = "../../modules/vpc"

  project_name = "elo-fraud"
  environment  = "staging"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  # VPC Endpoints (substituem NAT Gateway)
  enable_vpc_endpoints       = true   # S3, DynamoDB (gratuitos)
  enable_interface_endpoints = true   # ECR, SQS, STS, etc.

  # NAT Gateway desabilitado (usando endpoints)
  enable_nat_gateway = false
}
```

### Uso Completo (Producao)

```hcl
module "vpc" {
  source = "../../modules/vpc"

  project_name = "elo-fraud"
  environment  = "prod"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["sa-east-1a", "sa-east-1b", "sa-east-1c"]

  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  # DNS
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Endpoints para servicos AWS
  enable_vpc_endpoints       = true
  enable_interface_endpoints = true

  # NAT Gateway para APIs externas (se necessario)
  enable_nat_gateway = true
  single_nat_gateway = false  # HA: 1 NAT por AZ

  # ALB interno (via API Gateway + VPC Link)
  alb_internal = true

  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    ManagedBy   = "terraform"
    CostCenter  = "fraud-detection"
  }
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `project_name` | `string` | Sim | - | Nome do projeto |
| `environment` | `string` | Sim | - | Ambiente (dev, staging, prod) |
| `tags` | `map(string)` | Nao | `{}` | Tags adicionais |

### Rede

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `vpc_cidr` | `string` | Sim | - | CIDR block da VPC (ex: 10.0.0.0/16) |
| `availability_zones` | `list(string)` | Sim | - | Lista de AZs para usar |
| `public_subnet_cidrs` | `list(string)` | Sim | - | CIDRs das subnets publicas |
| `private_subnet_cidrs` | `list(string)` | Sim | - | CIDRs das subnets privadas |

### DNS

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `enable_dns_hostnames` | `bool` | Nao | `true` | Habilitar DNS hostnames |
| `enable_dns_support` | `bool` | Nao | `true` | Habilitar DNS support |

### NAT Gateway

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `enable_nat_gateway` | `bool` | Nao | `false` | Criar NAT Gateway |
| `single_nat_gateway` | `bool` | Nao | `true` | Usar 1 NAT para todas AZs (economia) |

### VPC Endpoints

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `enable_vpc_endpoints` | `bool` | Nao | `true` | Criar Gateway Endpoints (S3, DynamoDB) |
| `enable_interface_endpoints` | `bool` | Nao | `false` | Criar Interface Endpoints |

### ALB

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `alb_internal` | `bool` | Nao | `false` | ALB interno (apenas VPC) ou publico |

---

## Outputs

### VPC

| Output | Tipo | Descricao |
|--------|------|-----------|
| `vpc_id` | `string` | ID da VPC |
| `vpc_cidr` | `string` | CIDR block da VPC |
| `vpc_arn` | `string` | ARN da VPC |

### Subnets

| Output | Tipo | Descricao |
|--------|------|-----------|
| `public_subnet_ids` | `list(string)` | IDs das subnets publicas |
| `private_subnet_ids` | `list(string)` | IDs das subnets privadas |
| `public_subnet_cidrs` | `list(string)` | CIDRs das subnets publicas |
| `private_subnet_cidrs` | `list(string)` | CIDRs das subnets privadas |
| `availability_zones` | `list(string)` | AZs utilizadas |

### Gateways

| Output | Tipo | Descricao |
|--------|------|-----------|
| `internet_gateway_id` | `string` | ID do Internet Gateway |
| `nat_gateway_ids` | `list(string)` | IDs dos NAT Gateways |
| `nat_gateway_public_ips` | `list(string)` | IPs publicos dos NAT Gateways |

### Security Groups

| Output | Tipo | Descricao |
|--------|------|-----------|
| `security_group_alb_id` | `string` | ID do Security Group do ALB |
| `security_group_alb_internal` | `bool` | Indica se ALB e interno |
| `security_group_vpc_endpoints_id` | `string` | ID do SG dos Interface Endpoints |

### VPC Endpoints

| Output | Tipo | Descricao |
|--------|------|-----------|
| `vpc_endpoint_s3_id` | `string` | ID do VPC Endpoint S3 |
| `vpc_endpoint_dynamodb_id` | `string` | ID do VPC Endpoint DynamoDB |
| `vpc_endpoint_ecr_api_id` | `string` | ID do VPC Endpoint ECR API |
| `vpc_endpoint_ecr_dkr_id` | `string` | ID do VPC Endpoint ECR DKR |
| `vpc_endpoint_logs_id` | `string` | ID do VPC Endpoint CloudWatch Logs |
| `vpc_endpoint_sqs_id` | `string` | ID do VPC Endpoint SQS |
| `vpc_endpoint_sts_id` | `string` | ID do VPC Endpoint STS |
| `vpc_endpoint_ec2_id` | `string` | ID do VPC Endpoint EC2 |
| `vpc_endpoint_sagemaker_api_id` | `string` | ID do VPC Endpoint SageMaker API |
| `vpc_endpoint_sagemaker_runtime_id` | `string` | ID do VPC Endpoint SageMaker Runtime |
| `vpc_endpoint_firehose_id` | `string` | ID do VPC Endpoint Firehose |

### Route Tables

| Output | Tipo | Descricao |
|--------|------|-----------|
| `public_route_table_id` | `string` | ID da route table publica |
| `private_route_table_ids` | `list(string)` | IDs das route tables privadas |

### Summary

| Output | Tipo | Descricao |
|--------|------|-----------|
| `vpc_summary` | `object` | Resumo completo da configuracao |

---

## Operacoes

### Verificar VPC

```bash
# Listar VPCs
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=elo-fraud" \
  --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table \
  --region sa-east-1

# Detalhes da VPC
aws ec2 describe-vpcs \
  --vpc-ids vpc-xxxxxxxxx \
  --region sa-east-1
```

### Verificar Subnets

```bash
# Listar subnets da VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' \
  --output table \
  --region sa-east-1

# Ver IPs disponiveis por subnet
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'Subnets[*].[SubnetId,AvailableIpAddressCount]' \
  --output table \
  --region sa-east-1
```

### Verificar VPC Endpoints

```bash
# Listar VPC Endpoints
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,VpcEndpointType,State]' \
  --output table \
  --region sa-east-1

# Verificar status de um endpoint
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-xxxxxxxxx \
  --region sa-east-1
```

### Verificar NAT Gateway

```bash
# Listar NAT Gateways
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' \
  --output table \
  --region sa-east-1

# Verificar Elastic IPs
aws ec2 describe-addresses \
  --filters "Name=domain,Values=vpc" \
  --query 'Addresses[*].[AllocationId,PublicIp,AssociationId]' \
  --output table \
  --region sa-east-1
```

### Verificar Security Groups

```bash
# Listar Security Groups da VPC
aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'SecurityGroups[*].[GroupId,GroupName,Description]' \
  --output table \
  --region sa-east-1

# Ver regras de um SG
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=sg-xxxxxxxxx" \
  --region sa-east-1
```

### Verificar Route Tables

```bash
# Listar Route Tables
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0]]' \
  --output table \
  --region sa-east-1

# Ver rotas de uma route table
aws ec2 describe-route-tables \
  --route-table-ids rtb-xxxxxxxxx \
  --query 'RouteTables[0].Routes' \
  --region sa-east-1
```

### Testar Conectividade

```bash
# Testar conexao com S3 via endpoint (de dentro de uma instancia EC2)
aws s3 ls --region sa-east-1

# Testar conexao com DynamoDB via endpoint
aws dynamodb list-tables --region sa-east-1

# Verificar resolucao DNS de endpoint
nslookup s3.sa-east-1.amazonaws.com
nslookup ecr.sa-east-1.amazonaws.com
```

---

## Troubleshooting

### Erro: Pods EKS sem acesso a servicos AWS

**Sintoma**: Pods recebem timeout ao acessar S3, ECR, DynamoDB.

**Causas possiveis**:
1. VPC Endpoints nao configurados
2. Security Group dos endpoints bloqueando
3. Route table sem rota para endpoints

**Diagnostico**:
```bash
# Verificar se endpoints existem
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" \
  --query 'VpcEndpoints[*].ServiceName' \
  --region sa-east-1

# Verificar SG dos endpoints
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxxx \
  --query 'SecurityGroups[0].IpPermissions' \
  --region sa-east-1
```

**Solucao**:
- Habilitar `enable_interface_endpoints = true`
- Verificar se SG permite porta 443 do CIDR da VPC

---

### Erro: EKS nodes nao inicializam

**Sintoma**: Nodes ficam em `NotReady` ou nao aparecem.

**Causa**: Endpoints STS e EC2 nao configurados (obrigatorios para EKS).

**Solucao**:
```hcl
enable_interface_endpoints = true  # Inclui STS e EC2
```

---

### Erro: Subnets sem IPs disponiveis

**Sintoma**: `InsufficientFreeAddressesInSubnet`

**Diagnostico**:
```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-xxxxxxxxx \
  --query 'Subnets[0].AvailableIpAddressCount' \
  --region sa-east-1
```

**Solucao**:
- Aumentar CIDR das subnets (ex: /23 em vez de /24)
- Adicionar mais subnets em outras AZs
- Limpar ENIs orfaos de Lambda/EKS

---

### Erro: NAT Gateway em estado "failed"

**Sintoma**: NAT Gateway fica em estado `failed`.

**Causas possiveis**:
1. Elastic IP nao disponivel
2. Subnet nao e publica
3. Internet Gateway nao existe

**Diagnostico**:
```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids nat-xxxxxxxxx \
  --query 'NatGateways[0].[State,FailureMessage]' \
  --region sa-east-1
```

**Solucao**:
- Verificar se subnet tem rota para IGW
- Verificar se EIP esta alocado corretamente

---

### Erro: VPC Endpoint em estado "failed"

**Sintoma**: Endpoint fica em estado `failed` ou `rejected`.

**Diagnostico**:
```bash
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-xxxxxxxxx \
  --query 'VpcEndpoints[0].[State,LastError]' \
  --region sa-east-1
```

**Causas possiveis**:
1. Servico nao disponivel na regiao
2. Permissoes IAM insuficientes
3. VPC Endpoint Policy bloqueando

**Solucao**:
- Verificar disponibilidade do servico na regiao
- Verificar permissoes IAM

---

## Custos Estimados

### Componentes de Custo (sa-east-1)

| Componente | Calculo | Custo/Mes |
|------------|---------|-----------|
| **VPC** | Gratuito | $0 |
| **Internet Gateway** | Gratuito | $0 |
| **Subnets** | Gratuito | $0 |
| **Gateway Endpoints (S3, DynamoDB)** | Gratuito | $0 |
| **NAT Gateway** | $0.045/hora + $0.045/GB | ~$32 + dados |
| **Interface Endpoint** | $0.01/hora por AZ | ~$7.20/AZ |
| **Elastic IP (NAT)** | $0.005/hora (se nao associado) | ~$3.60 |

### Cenarios de Custo

| Cenario | Componentes | Custo/Mes |
|---------|-------------|-----------|
| **Minimo (sem NAT, sem Interface Endpoints)** | VPC + IGW + Gateway Endpoints | ~$0 |
| **Com Interface Endpoints (2 AZs, 9 endpoints)** | + 9 endpoints x 2 AZs | ~$130 |
| **Com NAT Gateway (1 NAT)** | + 1 NAT Gateway | ~$32 + dados |
| **Producao (3 AZs, NAT HA)** | + 9 endpoints x 3 AZs + 3 NATs | ~$290 + dados |

### Comparativo: NAT Gateway vs Interface Endpoints

| Volume de Dados | NAT Gateway | Interface Endpoints (9) |
|-----------------|-------------|-------------------------|
| **10 GB/mes** | $32 + $0.45 = ~$32 | ~$130 |
| **100 GB/mes** | $32 + $4.50 = ~$37 | ~$130 |
| **1 TB/mes** | $32 + $45 = ~$77 | ~$130 |
| **10 TB/mes** | $32 + $450 = ~$482 | ~$130 |

> **Recomendacao**: Para alto volume de dados com servicos AWS, Interface Endpoints sao mais economicos.

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **NAT Gateway desabilitado por padrao** | VPC Endpoints cobrem servicos AWS usados; economia de ~$32/mes |
| **Gateway Endpoints habilitados por padrao** | S3 e DynamoDB sao gratuitos e essenciais para o projeto |
| **Interface Endpoints opcionais** | Custo significativo (~$130/mes); habilitar conforme necessidade |
| **Single NAT Gateway padrao** | Economia em ambientes nao-producao; HA disponivel via variavel |
| **STS e EC2 endpoints** | Obrigatorios para EKS nodes em subnets privadas sem NAT |
| **SageMaker endpoints** | Permitem inferencia ML sem NAT Gateway |
| **Security Group ALB dinamico** | Flexibilidade entre ALB publico e interno |
| **DNS hostnames habilitado** | Necessario para resolucao de nomes dos endpoints |

---

## Referencias

### AWS Documentation

- [Amazon VPC User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/)
- [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [NAT Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [Route Tables](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html)

### Terraform Documentation

- [aws_vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc)
- [aws_subnet](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet)
- [aws_nat_gateway](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/nat_gateway)
- [aws_vpc_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint)
- [aws_security_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group)

### Best Practices

- [VPC Design Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)
- [EKS Networking Best Practices](https://aws.github.io/aws-eks-best-practices/networking/)
- [VPC Endpoint Best Practices](https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/best-practices.html)
