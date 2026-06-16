# Analise Completa: Modo VpcOnly no SageMaker Studio

**Data**: 2026-02-18
**Autor**: Gustavo Liebl Pereira
**Branch**: `gustaavolp-compasso`
**Conta AWS**: `888577064416` (single account, multi-region)

---

## 1. O que e o Modo VpcOnly

O SageMaker Studio Domain suporta dois modos de rede:

| Modo | Descricao |
|------|-----------|
| **PublicInternetOnly** | Apps do Studio acessam servicos AWS e internet diretamente via rede publica. Nao requer SG dedicado nem subnets privadas. |
| **VpcOnly** | Apps do Studio ficam isolados dentro da VPC. **Todo** trafego para servicos AWS deve sair via VPC Endpoints ou NAT Gateway. Nao ha acesso direto a internet. |

**VpcOnly e o modo recomendado pela AWS para ambientes de producao**, compliance e dados sensiveis, pois elimina o trafego via internet publica.

---

## 2. Estado Atual dos Ambientes

### 2.1. Resumo Comparativo

| Aspecto | DEV (us-east-1) | STAGING (sa-east-1) |
|---------|-----------------|---------------------|
| **Modo de Rede** | `PublicInternetOnly` | `VpcOnly` |
| **Subnets usadas** | Publicas (`10.0.1.0/24`, `10.0.2.0/24`) | Privadas (`10.1.11.0/24`, `10.1.12.0/24`) |
| **Security Group Studio** | Nao criado (count=0) | Criado com 5 regras |
| **vpc_cidr passada ao modulo** | Nao (default `""`) | Sim (`10.1.0.0/16`) |
| **Saida para AWS Services** | Internet direta | VPC Endpoints + NAT Gateway |
| **EFS (home dirs)** | Montado em subnets publicas | Montado em subnets privadas |
| **VPC CIDR** | `10.0.0.0/16` | `10.1.0.0/16` |

### 2.2. Configuracao no `terraform.tfvars`

**DEV** (`infra/environments/dev/mlops/terraform.tfvars`):
```hcl
app_network_access_type = "PublicInternetOnly"
```

**STAGING** (`infra/environments/staging/mlops/terraform.tfvars`):
```hcl
app_network_access_type = "VpcOnly"
```

### 2.3. Data Sources (o que cada ambiente le da Foundation)

**DEV** (`infra/environments/dev/mlops/data.tf`):
```hcl
locals {
  vpc_id            = data.terraform_remote_state.foundation.outputs.vpc_id
  public_subnet_ids = data.terraform_remote_state.foundation.outputs.public_subnet_ids
}
```

**STAGING** (`infra/environments/staging/mlops/data.tf`):
```hcl
locals {
  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids
  vpc_cidr           = data.terraform_remote_state.foundation.outputs.vpc_cidr
}
```

> **Ponto critico**: DEV nao importa `private_subnet_ids` nem `vpc_cidr`. Se fosse migrado para VpcOnly, esses locals precisariam ser adicionados ao `data.tf`.

### 2.4. Chamada do Modulo

**DEV** (`infra/environments/dev/mlops/main.tf`):
```hcl
module "sagemaker_studio" {
  # ...
  vpc_id     = local.vpc_id
  subnet_ids = local.public_subnet_ids  # <-- subnets PUBLICAS
  # vpc_cidr nao e passada (default "")
  app_network_access_type = var.app_network_access_type  # "PublicInternetOnly"
}
```

**STAGING** (`infra/environments/staging/mlops/main.tf`):
```hcl
module "sagemaker_studio" {
  # ...
  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnet_ids  # <-- subnets PRIVADAS
  vpc_cidr   = local.vpc_cidr            # "10.1.0.0/16"
  app_network_access_type = var.app_network_access_type  # "VpcOnly"
}
```

---

## 3. Topologia de Rede

### 3.1. DEV — PublicInternetOnly

```
                        Internet
                            |
                            v
                    +-------+-------+
                    | Internet GW   |
                    | (elo-fraud-   |
                    |  igw-dev)     |
                    +-------+-------+
                            |
        +-------------------+-------------------+
        |                                       |
+-------v--------+                    +---------v------+
| PUBLIC SUBNET  |                    | PUBLIC SUBNET  |
| us-east-1a     |                    | us-east-1b     |
| 10.0.1.0/24    |                    | 10.0.2.0/24    |
|                |                    |                |
| +------------+ |                    |                |
| | NAT GW     | |                    |                |
| +------------+ |                    |                |
|                |                    |                |
| +------------+ |                    | +------------+ |
| | SageMaker  | |                    | | SageMaker  | |
| | Studio     | |  (sem SG dedicado) | | Studio     | |
| | (EFS/Apps) | |                    | | (EFS/Apps) | |
| +-----+------+ |                    | +-----+------+ |
+-------|--------+                    +-------|--------+
        |                                     |
        +-------> Internet --> AWS Services <--+
                  (trafego publico direto)


+--PRIVATE SUBNETS (nao usadas pelo Studio em DEV)--+
| private-a: 10.0.11.0/24 | private-b: 10.0.12.0/24 |
| EKS Nodes, VPC Endpoints | EKS Nodes, VPC Endpoints|
+---------------------------+--------------------------+
```

**Fluxo de trafego DEV**:
- Apps do Studio -> Internet Gateway -> AWS Services (via internet publica)
- EFS home directories montados nas subnets publicas
- SG dedicado do Studio NAO e criado
- VPC Endpoints existem mas nao sao usados pelo Studio (estao nas subnets privadas)

### 3.2. STAGING — VpcOnly

```
                        Internet
                            |
                            v
                    +-------+-------+
                    | Internet GW   |
                    | (elo-fraud-   |
                    |  igw-staging) |
                    +-------+-------+
                            |
        +-------------------+-------------------+
        |                                       |
+-------v--------+                    +---------v------+
| PUBLIC SUBNET  |                    | PUBLIC SUBNET  |
| sa-east-1a     |                    | sa-east-1b     |
| 10.1.1.0/24    |                    | 10.1.2.0/24    |
|                |                    |                |
| +------------+ |                    |                |
| | NAT GW     | |                    |                |
| +------+-----+ |                    |                |
+--------|-------+                    +----------------+
         |
         | (fallback para servicos sem VPC Endpoint)
         |
+--------v---------+                  +-----------------+
| PRIVATE SUBNET   |                  | PRIVATE SUBNET  |
| sa-east-1a       |                  | sa-east-1b      |
| 10.1.11.0/24     |                  | 10.1.12.0/24    |
|                  |                  |                 |
| +-------------+  |                  | +-------------+ |
| | SageMaker   |  |                  | | SageMaker   | |
| | Studio      |  |                  | | Studio      | |
| | (EFS/Apps)  |  |                  | | (EFS/Apps)  | |
| +------+------+  |                  | +------+------+ |
|        |         |                  |        |        |
| Studio SG        |                  | Studio SG       |
| (HTTPS,NFS,DNS)  |                  | (HTTPS,NFS,DNS) |
|        |         |                  |        |        |
| +------v------+  |                  | +------v------+ |
| |VPC Endpoints|  |                  | |VPC Endpoints| |
| | (Interface) |  |                  | | (Interface) | |
| | SG: 443/tcp |  |                  | | SG: 443/tcp | |
| +------+------+  |                  | +------+------+ |
+--------|----------+                  +--------|--------+
         |                                      |
         +----> AWS Services (trafego privado) <+
              (S3, DynamoDB, SageMaker API,
               ECR, CW Logs, SQS, STS, etc.)
```

**Fluxo de trafego STAGING**:
1. Apps do Studio (subnets privadas) -> Studio SG (egress 443) -> VPC Endpoints -> AWS Services
2. Apps do Studio -> Studio SG (egress 443) -> NAT Gateway -> Internet (fallback para servicos sem VPCE)
3. EFS home directories -> Studio SG (NFS 2049) -> EFS mount targets (subnets privadas)
4. DNS -> Studio SG (UDP 53) -> VPC DNS resolver

---

## 4. Security Group do Studio (VpcOnly)

O modulo `sagemaker-studio` cria condicionalmente um Security Group quando `app_network_access_type = "VpcOnly"`.

**Arquivo**: `infra/modules/sagemaker-studio/main.tf` (linhas 153-248)

### 4.1. Regras Criadas

| Direcao | Recurso Terraform | Protocolo | Portas | Destino/Origem | Proposito |
|---------|------------------|-----------|--------|----------------|-----------|
| **Ingress** | `studio_self` | TCP | 0-65535 | Self (proprio SG) | Comunicacao entre apps do Studio |
| **Ingress** | `studio_nfs` | TCP | 2049 | Self (proprio SG) | NFS para EFS home directories (entre apps) |
| **Egress** | `studio_https` | TCP | 443 | `0.0.0.0/0` | HTTPS para AWS Services (via VPCE ou NAT) |
| **Egress** | `studio_nfs` | TCP | 2049 | VPC CIDR (`10.1.0.0/16`) | NFS egress para EFS mount targets |
| **Egress** | `studio_dns` | UDP | 53 | VPC CIDR (`10.1.0.0/16`) | DNS para resolucao de nomes |

### 4.2. Interacao com Security Group dos VPC Endpoints

O VPC Endpoint SG (`elo-fraud-vpc-endpoints-staging-*`) permite:

| Direcao | Protocolo | Portas | Origem | Proposito |
|---------|-----------|--------|--------|-----------|
| **Ingress** | TCP | 443 | VPC CIDR (`10.1.0.0/16`) | HTTPS de qualquer recurso da VPC |

**Cadeia completa de comunicacao**:
```
Studio App --> Studio SG (egress 443 to 0.0.0.0/0) --> VPC Endpoint SG (ingress 443 from 10.1.0.0/16) --> AWS Service
```

Funciona porque:
1. O egress do Studio SG permite 443 para qualquer destino
2. O ingress do VPC Endpoint SG permite 443 de qualquer IP da VPC CIDR
3. Os IPs dos VPC Endpoints estao dentro da VPC CIDR

### 4.3. EFS (Home Directories)

O SageMaker cria automaticamente um filesystem EFS para home directories (`/home/sagemaker-user/`). Em VpcOnly:

```
Studio App (10.1.11.x) --NFS 2049--> EFS Mount Target (10.1.11.y) (mesma subnet)
```

- O Studio SG permite **egress NFS (2049) para VPC CIDR**
- O Studio SG permite **ingress NFS (2049) self-referencing** (apps se comunicam entre si)
- O EFS mount target usa o proprio Studio SG (criado pelo SageMaker)

---

## 5. VPC Endpoints — Analise Completa

### 5.1. Endpoints Existentes (Foundation Stack)

Todos os VPC Endpoints sao criados no modulo VPC (`infra/modules/vpc/main.tf`) e estao disponiveis em **ambos** os ambientes:

| # | Endpoint | Tipo | Subnets | Proposito | Usado pelo Studio? |
|---|----------|------|---------|-----------|-------------------|
| 1 | `com.amazonaws.{region}.s3` | **Gateway** | Route tables (pub+priv) | S3 access | Sim (artifacts, data lake) |
| 2 | `com.amazonaws.{region}.dynamodb` | **Gateway** | Route tables (pub+priv) | DynamoDB access | Sim (feature store) |
| 3 | `com.amazonaws.{region}.ecr.api` | Interface | Privadas | ECR API (docker pull) | Indiretamente (custom images) |
| 4 | `com.amazonaws.{region}.ecr.dkr` | Interface | Privadas | ECR Docker registry | Indiretamente (custom images) |
| 5 | `com.amazonaws.{region}.logs` | Interface | Privadas | CloudWatch Logs | Sim (logs do Studio) |
| 6 | `com.amazonaws.{region}.sqs` | Interface | Privadas | SQS access | Sim (notebooks) |
| 7 | `com.amazonaws.{region}.sts` | Interface | Privadas | STS (IAM auth) | Sim (assume role) |
| 8 | `com.amazonaws.{region}.ec2` | Interface | Privadas | EC2 API | Indiretamente (network) |
| 9 | `com.amazonaws.{region}.sagemaker.api` | Interface | Privadas | SageMaker API | Sim (MLflow, training jobs) |
| 10 | `com.amazonaws.{region}.sagemaker.runtime` | Interface | Privadas | SageMaker Runtime | Potencial (inferencia) |
| 11 | `com.amazonaws.{region}.kinesis-firehose` | Interface | Privadas | Firehose | Nao diretamente |

### 5.2. Endpoints Recomendados (Faltantes)

Os endpoints abaixo **nao** existem na Foundation stack. O trafego para esses servicos **vai pelo NAT Gateway** (funciona, mas com custo e latencia adicionais):

| # | Endpoint Faltante | Tipo | Usado por | Impacto de nao ter | Prioridade |
|---|-------------------|------|-----------|---------------------|------------|
| 1 | `com.amazonaws.{region}.codecommit` | Interface | CodeCommit API (Git clone/push) | Trafego Git vai pelo NAT | Media |
| 2 | `com.amazonaws.{region}.git-codecommit` | Interface | Git over HTTPS para CodeCommit | Trafego Git vai pelo NAT | Media |
| 3 | `com.amazonaws.{region}.servicecatalog` | Interface | SageMaker Projects (ML Projects) | Criacao de projetos vai pelo NAT | Baixa |
| 4 | `com.amazonaws.{region}.bedrock-runtime` | Interface | Bedrock InvokeModel | Chamadas Bedrock vao pelo NAT | Baixa |
| 5 | `com.amazonaws.{region}.bedrock` | Interface | Bedrock API (list models, etc.) | API calls vao pelo NAT | Baixa |

> **Nota**: Nenhum desses endpoints e **bloqueante**. O NAT Gateway serve como fallback para qualquer servico sem VPC Endpoint dedicado. Os endpoints listados acima sao **otimizacoes** — reduzem custo de NAT e latencia.

### 5.3. Custo dos VPC Endpoints

| Tipo | Custo por Endpoint | Custo por AZ | Atual (11 endpoints, 2 AZs) |
|------|--------------------|-------------|------------------------------|
| Gateway (S3, DynamoDB) | **Gratuito** | - | $0/mes |
| Interface | ~$7.20/mes | por AZ | ~$7.20 x 9 x 2 = **~$129.60/mes** |

> Os 9 Interface Endpoints em 2 AZs custam ~$129.60/mes por ambiente. Cada endpoint adicional acrescenta ~$14.40/mes (2 AZs).

---

## 6. Fluxo de Trafego Detalhado (STAGING VpcOnly)

### 6.1. Notebook acessa S3 (leitura de dados)

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress 443 permitido para 0.0.0.0/0)
3. --> Route Table privada intercepta trafego para S3
4. --> S3 Gateway Endpoint (sem custo)
5. --> Amazon S3
```

### 6.2. Notebook acessa DynamoDB (feature store)

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress 443 permitido para 0.0.0.0/0)
3. --> Route Table privada intercepta trafego para DynamoDB
4. --> DynamoDB Gateway Endpoint (sem custo)
5. --> Amazon DynamoDB
```

### 6.3. Notebook acessa MLflow (`mlflow.set_tracking_uri`)

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress 443 permitido)
3. --> SageMaker API VPC Endpoint (10.1.11.y)
4. --> VPC Endpoint SG (ingress 443 from 10.1.0.0/16)
5. --> Amazon SageMaker API
6. --> MLflow Tracking Server (managed)
```

### 6.4. Notebook faz Git clone do CodeCommit

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress 443 permitido)
3. --> Route Table privada (nao ha VPCE para codecommit)
4. --> NAT Gateway (10.1.1.x, subnet publica)
5. --> Internet Gateway
6. --> AWS CodeCommit API
```

> Este fluxo funciona mas tem custo de NAT ($0.045/GB). Um VPCE para `codecommit` + `git-codecommit` eliminaria esse custo.

### 6.5. Notebook envia mensagem para SQS

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress 443 permitido)
3. --> SQS VPC Endpoint (10.1.11.y)
4. --> VPC Endpoint SG (ingress 443 from 10.1.0.0/16)
5. --> Amazon SQS
```

### 6.6. EFS Home Directory (leitura/escrita de arquivos)

```
1. Studio App (10.1.11.x)
2. --> Studio SG (egress NFS 2049 para 10.1.0.0/16)
3. --> EFS Mount Target (10.1.11.y, mesma subnet)
4. --> Amazon EFS (dentro da VPC, sem custo de trafego)
```

---

## 7. O que o Terraform Cria/Nao Cria por Modo

### 7.1. Recursos condicionais (`count = VpcOnly ? 1 : 0`)

| Recurso | PublicInternetOnly (DEV) | VpcOnly (STAGING) |
|---------|-------------------------|-------------------|
| `aws_security_group.studio` | NAO criado | Criado |
| `aws_vpc_security_group_ingress_rule.studio_self` | NAO criado | Criado |
| `aws_vpc_security_group_ingress_rule.studio_nfs` | NAO criado | Criado |
| `aws_vpc_security_group_egress_rule.studio_https` | NAO criado | Criado |
| `aws_vpc_security_group_egress_rule.studio_nfs` | NAO criado | Criado |
| `aws_vpc_security_group_egress_rule.studio_dns` | NAO criado | Criado |

### 7.2. Configuracao no Domain

| Atributo | PublicInternetOnly (DEV) | VpcOnly (STAGING) |
|----------|-------------------------|-------------------|
| `app_network_access_type` | `"PublicInternetOnly"` | `"VpcOnly"` |
| `default_user_settings.security_groups` | `null` | `[studio_sg_id]` |

### 7.3. Recursos que sao criados em AMBOS os modos

- IAM Role + Policy Attachments (identicos)
- CloudWatch Log Group (identico)
- SageMaker Domain (config de rede diferente)
- User Profiles (identicos)
- EFS (criado automaticamente pelo SageMaker, nao pelo Terraform)

---

## 8. Proximos Passos — Deploy de STAGING (VpcOnly)

### Pre-requisitos

- Terraform v1.14.x instalado
- AWS CLI configurado para conta `888577064416`
- Acesso ao bucket de state: `elo-fraud-terraform-state-888577064416-us-east-1`
- Profile com permissao para `ec2:*SecurityGroup*`, `sagemaker:*Domain*`, `iam:*`

### Passo 1: Configurar credenciais para STAGING

```bash
aws sts get-caller-identity
# Esperado: Account = 888577064416

export AWS_DEFAULT_REGION=sa-east-1
```

### Passo 2: Verificar que a Foundation ja esta aplicada

A stack MLOps depende de outputs da Foundation (VPC, subnets). Confirmar:

```bash
# Verificar state da Foundation STAGING
aws s3 ls s3://elo-fraud-terraform-state-888577064416-us-east-1/staging/foundation/

# Deve listar terraform.tfstate
```

Verificar que VPC e subnets existem:

```bash
# VPC
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=elo-fraud-vpc-staging" \
  --query 'Vpcs[0].{VpcId:VpcId,CidrBlock:CidrBlock,State:State}' \
  --output table

# Subnets privadas
aws ec2 describe-subnets \
  --filters "Name=tag:Type,Values=private" "Name=tag:Environment,Values=staging" \
  --query 'Subnets[].{SubnetId:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}' \
  --output table
```

### Passo 3: Verificar VPC Endpoints ativos

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=tag:Environment,Values=staging" \
  --query 'VpcEndpoints[].{Service:ServiceName,State:State,Type:VpcEndpointType}' \
  --output table
```

Resultado esperado: **11 endpoints** (2 Gateway + 9 Interface), todos com `State=available`.

### Passo 4: Verificar NAT Gateway ativo

```bash
aws ec2 describe-nat-gateways \
  --filter "Name=tag:Name,Values=elo-fraud-nat-staging" \
  --query 'NatGateways[0].{State:State,PublicIp:NatGatewayAddresses[0].PublicIp,SubnetId:SubnetId}' \
  --output table
```

Resultado esperado: `State=available`, com IP publico alocado.

> **Critico**: Se o NAT Gateway nao estiver ativo, o Studio em VpcOnly nao conseguira acessar servicos sem VPC Endpoint (ex: CodeCommit, Bedrock).

### Passo 5: Navegar ate a stack MLOps STAGING

```bash
cd infra/environments/staging/mlops
```

### Passo 6: Inicializar Terraform

```bash
terraform init
```

> O backend do state esta em `us-east-1` (bucket centralizado). O `terraform init` precisa resolver o state bucket em `us-east-1`.

### Passo 7: Validar

```bash
terraform validate
```

### Passo 8: Executar o Plan

```bash
terraform plan -out=plan-staging-mlops.tfplan
```

**O que verificar CUIDADOSAMENTE no plan**:

1. **Security Group Studio**: Deve aparecer `aws_security_group.studio[0]` como **novo** (se ainda nao existe)
2. **5 SG Rules**: As 5 regras (2 ingress + 3 egress) devem aparecer como **novas**
3. **Domain `app_network_access_type`**: Deve mostrar `"VpcOnly"`
4. **Domain `security_groups`**: Deve referenciar o SG criado
5. **Domain `subnet_ids`**: Deve listar as subnets **privadas** (`10.1.11.0/24`, `10.1.12.0/24`)

**ALERTA**: Se o plan mostrar **changes no Domain existente** (ex: mudanca de `PublicInternetOnly` para `VpcOnly`), isso pode **forcar recreacao do Domain** dependendo da versao do provider. Verificar se ha `# forces replacement` no plan.

> **Alteracao de `app_network_access_type` em um Domain existente causa REPLACE (destroy + create)**. Isso deleta todos os User Profiles, apps e EFS home directories. Se o Domain ja existe em um modo, **NAO** mude para outro sem planejamento de migracao.

### Passo 9: Revisar o Plan

```bash
terraform show plan-staging-mlops.tfplan
```

### Passo 10: Aplicar

```bash
terraform apply plan-staging-mlops.tfplan
```

### Passo 11: Verificar Security Group criado

```bash
# Listar SGs do Studio
aws ec2 describe-security-groups \
  --filters "Name=tag:Component,Values=SageMaker-Studio-SecurityGroup" \
  --query 'SecurityGroups[].{GroupId:GroupId,GroupName:GroupName,VpcId:VpcId}' \
  --output table --region sa-east-1

# Ver regras do SG
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=tag:Component,Values=SageMaker-Studio-SecurityGroup" \
  --query 'SecurityGroups[0].GroupId' --output text --region sa-east-1)

echo "=== INGRESS ==="
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$SG_ID" \
  --query 'SecurityGroupRules[?!IsEgress].{Port:FromPort,Protocol:IpProtocol,Source:ReferencedGroupInfo.GroupId||CidrIpv4}' \
  --output table --region sa-east-1

echo "=== EGRESS ==="
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$SG_ID" \
  --query 'SecurityGroupRules[?IsEgress].{Port:FromPort,Protocol:IpProtocol,Destination:CidrIpv4}' \
  --output table --region sa-east-1
```

### Passo 12: Verificar o Domain

```bash
DOMAIN_ID=$(aws sagemaker list-domains \
  --query 'Domains[?DomainName==`elo-fraud-studio-staging`].DomainId' \
  --output text --region sa-east-1)

aws sagemaker describe-domain \
  --domain-id $DOMAIN_ID \
  --query '{Status:Status,NetworkAccess:AppNetworkAccessType,SecurityGroups:DefaultUserSettings.SecurityGroups,SubnetIds:SubnetIds}' \
  --output json --region sa-east-1
```

Resultado esperado:
```json
{
  "Status": "InService",
  "NetworkAccess": "VpcOnly",
  "SecurityGroups": ["sg-xxxxxxxxxx"],
  "SubnetIds": ["subnet-aaaa", "subnet-bbbb"]
}
```

### Passo 13: Testar conectividade do Studio

```bash
# Gerar URL de acesso
aws sagemaker create-presigned-domain-url \
  --domain-id $DOMAIN_ID \
  --user-profile-name elo-fraud-ml-user \
  --region sa-east-1
```

Dentro do notebook, testar:

```python
# Teste 1: S3 (via Gateway Endpoint)
import boto3
s3 = boto3.client('s3')
s3.list_buckets()  # Deve funcionar

# Teste 2: DynamoDB (via Gateway Endpoint)
ddb = boto3.client('dynamodb')
ddb.list_tables()  # Deve funcionar

# Teste 3: MLflow (via SageMaker API Endpoint)
import mlflow
mlflow.set_tracking_uri("aws://sagemaker/elo-fraud-mlflow-staging")
mlflow.search_experiments()  # Deve funcionar

# Teste 4: SQS (via Interface Endpoint)
sqs = boto3.client('sqs')
sqs.list_queues()  # Deve funcionar

# Teste 5: CloudWatch Logs (via Interface Endpoint)
logs = boto3.client('logs')
logs.describe_log_groups(limit=5)  # Deve funcionar
```

---

## 9. Proximos Passos — Se DEV Precisar Migrar para VpcOnly

> **ATENCAO**: Mudar `app_network_access_type` de `PublicInternetOnly` para `VpcOnly` em um Domain existente **causa REPLACE (destroy+create)**, perdendo User Profiles, apps e EFS. Planejar migracao com cuidado.

### 9.1. Alteracoes necessarias no DEV

| Arquivo | Alteracao |
|---------|-----------|
| `infra/environments/dev/mlops/terraform.tfvars` | `app_network_access_type = "VpcOnly"` |
| `infra/environments/dev/mlops/data.tf` | Adicionar `private_subnet_ids` e `vpc_cidr` nos locals |
| `infra/environments/dev/mlops/main.tf` | Mudar `subnet_ids` para `local.private_subnet_ids`, adicionar `vpc_cidr = local.vpc_cidr` |

### 9.2. Alteracao em `data.tf`

```hcl
# ADICIONAR aos locals existentes:
locals {
  aws_account_id     = data.aws_caller_identity.current.account_id
  vpc_id             = data.terraform_remote_state.foundation.outputs.vpc_id
  public_subnet_ids  = data.terraform_remote_state.foundation.outputs.public_subnet_ids  # manter (usado por outros?)
  private_subnet_ids = data.terraform_remote_state.foundation.outputs.private_subnet_ids  # NOVO
  vpc_cidr           = data.terraform_remote_state.foundation.outputs.vpc_cidr             # NOVO
}
```

### 9.3. Alteracao em `main.tf`

```hcl
module "sagemaker_studio" {
  # ...
  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnet_ids  # MUDANCA: public -> private
  vpc_cidr   = local.vpc_cidr            # NOVO

  app_network_access_type = var.app_network_access_type  # agora sera "VpcOnly"
  # ...
}
```

### 9.4. Procedimento de Migracao (se necessario)

1. **Exportar dados do EFS** (notebooks, configs) antes do destroy
2. **Deletar todos os apps e user profiles** manualmente (ou via Terraform)
3. Executar `terraform apply` — vai destruir o Domain antigo e criar novo
4. Recriar User Profiles (automatico via Terraform)
5. **Reimportar dados para o novo EFS**
6. Testar conectividade (mesmos testes da Secao 8, Passo 13)

> **Recomendacao**: Manter DEV em `PublicInternetOnly` para desenvolvimento rapido. VpcOnly e essencial para STAGING/PROD por compliance, mas agrega complexidade desnecessaria em DEV.

---

## 10. Pontos de Atencao e Riscos

### 10.1. Domain Replacement (CRITICO)

| Risco | Mudar `app_network_access_type` em Domain existente |
|-------|------------------------------------------------------|
| **Impacto** | Destroy + Create do Domain. Perde EFS, User Profiles, Apps |
| **Mitigacao** | Nunca mudar o modo de rede de um Domain ja em uso sem backup do EFS |
| **Como verificar** | `terraform plan` mostrara `# forces replacement` se aplicavel |

### 10.2. NAT Gateway Single Point of Failure

| Risco | NAT Gateway unico em AZ-A |
|-------|---------------------------|
| **Impacto** | Se NAT falhar, Studio perde acesso a servicos sem VPC Endpoint (CodeCommit, Bedrock) |
| **Mitigacao** | VPC Endpoints cobrem os servicos criticos (S3, DynamoDB, SageMaker API, SQS, Logs, STS) |
| **Melhoria futura** | Adicionar segundo NAT em AZ-B para HA (custo: +$32/mes) |

### 10.3. EFS em Subnets Privadas

| Risco | EFS mount targets em subnets privadas |
|-------|---------------------------------------|
| **Impacto** | Nenhum — e o comportamento esperado em VpcOnly |
| **Verificacao** | NFS 2049 permitido no Studio SG (egress para VPC CIDR) |

### 10.4. VPC Endpoints — Custo vs Beneficio

| Cenario | Custo mensal | Servicos cobertos |
|---------|-------------|-------------------|
| Atual (9 Interface + 2 Gateway) | ~$129.60 | S3, DDB, ECR, Logs, SQS, STS, EC2, SageMaker API/Runtime, Firehose |
| + CodeCommit (2 endpoints) | ~$158.40 | + Git operations |
| + Service Catalog (1 endpoint) | ~$172.80 | + SageMaker Projects |
| + Bedrock (2 endpoints) | ~$201.60 | + Bedrock models |

> O custo de NAT para o trafego residual e tipicamente menor que adicionar mais endpoints, a menos que o volume de trafego seja alto.

### 10.5. Limite de Policies por Role (AWS)

Uma IAM Role pode ter no maximo **20 managed policies** anexadas (hard limit). O estado atual:

| Role | Managed Policies | Margem |
|------|-----------------|--------|
| Studio Execution Role | 9 | 11 restantes |
| MLflow Execution Role | 9 | 11 restantes |

---

## 11. Troubleshooting

### 11.1. Studio nao abre em VpcOnly

**Sintoma**: Timeout ao abrir Studio ou erro "Unable to start application"

**Diagnostico**:
```bash
# 1. Verificar SG do Studio
aws ec2 describe-security-groups --group-ids sg-xxx --region sa-east-1

# 2. Verificar VPC Endpoints estao "available"
aws ec2 describe-vpc-endpoints \
  --filters "Name=tag:Environment,Values=staging" \
  --query 'VpcEndpoints[].{Service:ServiceName,State:State}' \
  --output table --region sa-east-1

# 3. Verificar NAT Gateway
aws ec2 describe-nat-gateways \
  --filter "Name=tag:Name,Values=elo-fraud-nat-staging" \
  --query 'NatGateways[0].State' --output text --region sa-east-1

# 4. Verificar Route Table das subnets privadas
aws ec2 describe-route-tables \
  --filters "Name=tag:Type,Values=private" "Name=tag:Environment,Values=staging" \
  --query 'RouteTables[0].Routes[].{Dest:DestinationCidrBlock,NAT:NatGatewayId,VPCE:GatewayId}' \
  --output table --region sa-east-1
```

**Causas comuns**:
1. VPC Endpoint para `sagemaker.api` nao esta `available`
2. SG do VPC Endpoint nao permite ingress 443 da VPC CIDR
3. NAT Gateway em estado `failed` ou `deleted`
4. Route Table privada sem rota para NAT Gateway

### 11.2. Notebook nao acessa S3

**Diagnostico** (dentro do notebook):
```python
import boto3
try:
    s3 = boto3.client('s3')
    s3.list_buckets()
except Exception as e:
    print(f"Erro: {e}")
```

**Causas comuns**:
1. S3 Gateway Endpoint nao esta na route table das subnets privadas
2. IAM Role sem `AmazonS3FullAccess`

**Verificacao**:
```bash
# Verificar S3 VPC Endpoint nas route tables
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=com.amazonaws.sa-east-1.s3" \
  --query 'VpcEndpoints[0].RouteTableIds' --output json --region sa-east-1
```

### 11.3. MLflow nao conecta (`sagemaker-mlflow:*`)

**Diagnostico** (dentro do notebook):
```python
import mlflow
mlflow.set_tracking_uri("aws://sagemaker/elo-fraud-mlflow-staging")
try:
    mlflow.search_experiments()
except Exception as e:
    print(f"Erro: {e}")
```

**Causas comuns**:
1. VPC Endpoint para `sagemaker.api` nao existe ou nao esta `available`
2. IAM Role sem inline policy `SageMakerMLflowFullAccess` (`sagemaker-mlflow:*`)
3. MLflow Tracking Server nao esta em estado `Created`

**Verificacao**:
```bash
# Estado do MLflow
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-staging \
  --query '{Status:TrackingServerStatus,Url:TrackingServerUrl}' \
  --output json --region sa-east-1
```

### 11.4. Git clone do CodeCommit falha

**Sintoma**: Timeout ao fazer `git clone` dentro do Studio

**Causa**: Nao ha VPC Endpoint para `codecommit` / `git-codecommit`. Trafego vai pelo NAT.

**Diagnostico**:
```bash
# Verificar NAT Gateway ativo
aws ec2 describe-nat-gateways \
  --filter "Name=tag:Name,Values=elo-fraud-nat-staging" \
  --query 'NatGateways[0].State' --region sa-east-1
```

**Solucao**: Se o NAT esta ativo e ainda falha, pode ser DNS. Verificar:
```bash
# DNS support na VPC
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-xxx \
  --attribute enableDnsSupport --region sa-east-1

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-xxx \
  --attribute enableDnsHostnames --region sa-east-1
```

Ambos devem retornar `true`.

### 11.5. DNS nao resolve dentro do Studio

**Causa**: Studio SG nao permite egress UDP 53.

**Verificacao**:
```bash
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=$SG_ID" \
  --query 'SecurityGroupRules[?IsEgress && IpProtocol==`udp`]' \
  --output table --region sa-east-1
```

Deve mostrar regra egress UDP 53 para VPC CIDR.

---

## 12. Resumo da Arquitetura Final (STAGING VpcOnly)

```
+==============================================================================+
|                     STAGING - sa-east-1 - VpcOnly                            |
+==============================================================================+
|                                                                              |
|  VPC: 10.1.0.0/16 (DNS Support: ON, DNS Hostnames: ON)                      |
|                                                                              |
|  +--PUBLIC SUBNETS------------------------------------------------------+    |
|  | sa-east-1a: 10.1.1.0/24  |  sa-east-1b: 10.1.2.0/24                 |    |
|  | [NAT GW] [EIP]           |                                           |    |
|  | [Internet GW route]      |  [Internet GW route]                      |    |
|  +------------------------------------------------------------------+    |    |
|                                                                          |    |
|  +--PRIVATE SUBNETS-----------------------------------------------------+    |
|  | sa-east-1a: 10.1.11.0/24  |  sa-east-1b: 10.1.12.0/24               |    |
|  |                            |                                          |    |
|  | [SageMaker Studio Domain]  |  [SageMaker Studio Domain]               |    |
|  |   - User: elo-fraud-ml-user|    (HA across AZs)                       |    |
|  |   - Role: mlflow exec role |                                          |    |
|  |   - SG: studio-sg          |  - SG: studio-sg                         |    |
|  |                            |                                          |    |
|  | [EFS Mount Target]         |  [EFS Mount Target]                      |    |
|  |   /home/sagemaker-user/    |    /home/sagemaker-user/                 |    |
|  |                            |                                          |    |
|  | [EKS Nodes]                |  [EKS Nodes]                             |    |
|  |   inference + process pods |    inference + process pods              |    |
|  |                            |                                          |    |
|  | [VPC Interface Endpoints]  |  [VPC Interface Endpoints]               |    |
|  |   ECR API, ECR DKR         |    ECR API, ECR DKR                      |    |
|  |   CW Logs, SQS, STS        |    CW Logs, SQS, STS                    |    |
|  |   EC2, SageMaker API       |    EC2, SageMaker API                    |    |
|  |   SageMaker Runtime        |    SageMaker Runtime                     |    |
|  |   Firehose                 |    Firehose                              |    |
|  |                            |                                          |    |
|  | [NAT GW route: 0.0.0.0/0] |  [NAT GW route: 0.0.0.0/0]              |    |
|  +-------------------------------------------------------------------+   |    |
|                                                                          |    |
|  +--GATEWAY ENDPOINTS (route table level)-------------------------------+    |
|  | S3 Gateway Endpoint (ambas route tables)                              |    |
|  | DynamoDB Gateway Endpoint (ambas route tables)                        |    |
|  +-----------------------------------------------------------------------+    |
|                                                                              |
+==============================================================================+

Fluxos de saida do Studio (prioridade):
  1. S3, DynamoDB         --> Gateway Endpoints (gratuito, latencia minima)
  2. SageMaker, SQS, etc. --> Interface Endpoints (custo fixo, latencia baixa)
  3. CodeCommit, Bedrock   --> NAT Gateway --> Internet (custo por GB)
```
