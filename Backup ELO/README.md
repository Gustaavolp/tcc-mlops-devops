# Documentação Completa — Espelhamento SMUS no Terraform
## poc-catalogo-gov-dados | Amazon SageMaker Unified Studio

> **Repositório:** `poc-esteira-compass-repo`
> **Data:** Fevereiro 2026
> **Objetivo:** Registrar o ambiente AWS SageMaker Unified Studio existente em Terraform (IaC), vinculando o state ao que já existe na conta sem recriar nada.

---

## Índice

1. [Contexto e Objetivo](#1-contexto-e-objetivo)
2. [Conceitos Fundamentais](#2-conceitos-fundamentais)
3. [Inventário do Ambiente Real](#3-inventário-do-ambiente-real)
4. [Comandos AWS CLI Utilizados](#4-comandos-aws-cli-utilizados)
5. [Análise do Template Oficial AWS](#5-análise-do-template-oficial-aws)
6. [Decisões de Implementação](#6-decisões-de-implementação)
7. [Estrutura de Arquivos Terraform](#7-estrutura-de-arquivos-terraform)
8. [Detalhamento de Cada Arquivo](#8-detalhamento-de-cada-arquivo)
9. [Recursos Terraform Mapeados](#9-recursos-terraform-mapeados)
10. [Fluxo de Import — Como Funciona](#10-fluxo-de-import---como-funciona)
11. [Próximos Passos](#11-próximos-passos)
12. [Informações Bloqueadas](#12-informações-bloqueadas)
13. [Referência Rápida de IDs](#13-referência-rápida-de-ids)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Contexto e Objetivo

### O que é o SageMaker Unified Studio (SMUS)?

O Amazon SageMaker Unified Studio (SMUS) é a evolução do Amazon DataZone. Ele unifica em uma única interface o catálogo de dados, governança, projetos de ML, queries SQL, workflows e muito mais. Internamente, os recursos são criados via **Amazon DataZone API**, mas a interface é o console do SageMaker Unified Studio.

**Componentes principais do SMUS:**

```
Domínio (Domain)
├── Domain Units (Subdomínios) ← equivalente a "departamentos" ou "áreas"
│   ├── Domain Unit A (ex: CRM)
│   └── Domain Unit B (ex: Fábrica Campanhas)
├── Blueprints (Configurações de ambiente disponíveis)
│   ├── Tooling → SageMaker Studio, Athena, S3
│   ├── DataLake → Glue Database, Athena
│   ├── LakehouseCatalog → SageMaker Lakehouse
│   └── RedshiftServerless → Amazon Redshift
├── Project Profiles (Modelos de projeto)
│   └── Default → define quais ambientes cada projeto terá
└── Projetos (Projects) ← onde os usuários trabalham
    ├── poc_catalogo_gov_dados
    ├── poc_catalogo_tableau
    ├── poc_catalogo_gov_dados_crm
    └── poc_catalogo_gov_dados_fabrica_campanhas
```

### O Problema

O ambiente já existia na AWS, criado manualmente via console. A tarefa era **espelhar este ambiente em Terraform** — ou seja, criar o código IaC que representa exatamente o que está na AWS, para que futuros ambientes possam ser criados de forma automatizada e repetível.

### A Estratégia

Em vez de recriar os recursos do zero (o que destruiria e recriaria tudo), utilizamos a funcionalidade de **`terraform import`** para vincular os recursos existentes ao state do Terraform. O código declara os recursos e o import associa cada declaração ao recurso real na AWS.

---

## 2. Conceitos Fundamentais

### 2.1 Terraform Import (Nativo — `import {}` blocks)

A partir do Terraform 1.5, é possível usar blocos `import {}` diretamente no código HCL. O fluxo é:

```
1. Você escreve a declaração do recurso em main.tf
2. Você escreve o bloco import em imports.tf
3. terraform plan lê o estado real da AWS e compara com seu código
4. terraform apply vincula o recurso AWS ao state do Terraform
```

**Formato básico:**
```hcl
import {
  to = tipo_recurso.nome_local
  id = "identificador-do-recurso-na-aws"
}
```

**Por que isso é importante?** Sem o import, se você declarar um recurso que já existe na AWS e rodar `terraform apply`, o Terraform tentará criar um novo recurso — o que vai falhar com erro de conflito de nome ou criar um duplicado.

### 2.2 Dois Providers Terraform (aws vs awscc)

Este projeto usa **dois providers diferentes** para acessar a AWS:

| Provider | Pacote | Quando usar |
|----------|--------|-------------|
| `hashicorp/aws` | `aws` | Recursos mais antigos/maduros. API direta da AWS. |
| `hashicorp/awscc` | `awscc` | Recursos novos via CloudControl API. Necessário para DataZone/SMUS. |

**Por que dois?** O Amazon DataZone/SMUS é um serviço relativamente novo. Muitos dos seus recursos só estão disponíveis via **CloudControl API** (awscc), enquanto alguns (como `aws_datazone_environment_blueprint_configuration`) já foram incorporados ao provider `aws` clássico.

**Diferença no formato do import ID:**
- Provider `aws`: usa `/` como separador → `dzd-drrjoqtodsc8o9/3owsbi7jjppvc9`
- Provider `awscc`: usa `|` como separador → `dzd-drrjoqtodsc8o9|dgfm4s2lizz44p`

### 2.3 Data Sources vs Resources

```hcl
# Data Source — lê algo que JÁ EXISTE na AWS (não gerencia o ciclo de vida)
data "aws_iam_role" "provisioning_role" {
  name = "AmazonSageMakerProvisioning-679740497328"
}

# Resource — Terraform GERENCIA o ciclo de vida deste recurso
resource "aws_iam_role" "sagemaker_manage_access" {
  name = "AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9"
  ...
}
```

**Regra usada neste projeto:**
- Se o nome do recurso **bate** com o padrão do template → `resource` (importamos)
- Se o nome do recurso **não bate** com o padrão → `data` (só referenciamos)

### 2.4 Módulos Terraform

Módulos são "funções reutilizáveis" que agrupam recursos. Neste projeto reutilizamos dois módulos do template oficial AWS:

```hcl
module "blueprint_policy_grants" {
  source = "Unified-Studio-for-Amazon-Sagemaker/terraform/constructs/create-blueprint-policy-grant"
  ...
}
```

O `source` aqui aponta para um **caminho relativo** dentro do repositório. Como o Terraform é inicializado na raiz do repositório, os módulos ficam em `Unified-Studio-for-Amazon-Sagemaker/terraform/constructs/`.

### 2.5 Blueprints vs Project Profiles vs Projetos

| Conceito | O que é | Terraform |
|----------|---------|-----------|
| **Blueprint** | "Template" de ambiente disponível no domínio (ex: Tooling, DataLake) | `aws_datazone_environment_blueprint_configuration` |
| **Blueprint Policy Grant** | Permissão para projetos criarem ambientes do blueprint | `awscc_datazone_policy_grant` (entity_type=ENVIRONMENT_BLUEPRINT_CONFIGURATION) |
| **Project Profile** | "Modelo de projeto" — define quais ambientes serão criados automaticamente | `awscc_datazone_project_profile` |
| **Project Profile Policy Grant** | Permissão para usuários criarem projetos baseados no profile | `awscc_datazone_policy_grant` (entity_type=DOMAIN_UNIT) |
| **Project** | Projeto de trabalho onde usuários colaboram | `awscc_datazone_project` |
| **Domain Unit** | Subdivisão do domínio (subdomínio/área) | `awscc_datazone_domain_unit` |

---

## 3. Inventário do Ambiente Real

### 3.1 Identificadores Principais

| Recurso | Valor |
|---------|-------|
| **Conta AWS** | `679740497328` |
| **Região** | `us-east-2` (Ohio) |
| **Profile CLI** | `elo2` (SSO-GovDados-Devs) |
| **Domain ID** | `dzd-drrjoqtodsc8o9` |
| **Domain Name** | `poc-catalogo-gov-dados` |
| **Domain Version** | `V2` |
| **SSO** | `DISABLED` |
| **Root Domain Unit ID** | `6uns306w58f9yh` |

### 3.2 Roles IAM

| Papel | Nome | ARN | Gerenciado por |
|-------|------|-----|----------------|
| Domain Execution | `AmazonSageMakerAdminIAMExecutionRole_1` | `arn:aws:iam::679740497328:role/service-role/AmazonSageMakerAdminIAMExecutionRole_1` | `data source` |
| Domain Service | `AmazonSageMakerAdminIAMExecutionRole_1` | (mesma role acima) | `data source` |
| ManageAccess | `AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9` | `arn:aws:iam::679740497328:role/service-role/AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9` | `resource` (importado) |
| Provisioning | `AmazonSageMakerProvisioning-679740497328` | `arn:aws:iam::679740497328:role/service-role/AmazonSageMakerProvisioning-679740497328` | `data source` |

**Por que ManageAccess é `resource` e Provisioning é `data source`?**

O template oficial cria:
- ManageAccess: `AmazonSageMakerManageAccess-{region}-{domain_id}` → `AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9` ✅ **BATE**
- Provisioning: `AmazonSageMakerProvisioning-{account_id}-{domain_id}` → `AmazonSageMakerProvisioning-679740497328-dzd-drrjoqtodsc8o9` ❌ **NÃO BATE** (real é sem domain_id)

### 3.3 Infraestrutura de Rede e Storage

| Recurso | Valor |
|---------|-------|
| **VPC** | `vpc-079d52c4150206c04` |
| **Subnet 1** | `subnet-0374c7d945dfdbccd` (us-east-2b) |
| **Subnet 2** | `subnet-01ea650dbcbe8cdc5` (us-east-2c) |
| **Availability Zones** | `us-east-2b,us-east-2c` |
| **S3 Bucket** | `amazon-sagemaker-679740497328-us-east-2-00d422527895` |

**Por que o S3 é hardcoded?**

O template tenta gerar o nome com:
```hcl
"amazon-sagemaker-${account_id}-${region}-${replace(domain_id, "dzd_", "")}"
```

Porém o `domain_id` real usa **hífen** (`dzd-drrjoqtodsc8o9`), não underscore. O `replace` procura `"dzd_"` e não encontra nada. O nome real do bucket é completamente diferente do que a fórmula geraria. Por isso o nome é hardcoded via variável.

### 3.4 Blueprints Habilitados (4 no total)

| Nome | Blueprint ID | ManageAccess Role | Provisioning Role | Params |
|------|-------------|-------------------|-------------------|--------|
| Tooling | `3owsbi7jjppvc9` | AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9 | AmazonSageMakerProvisioning-679740497328 | VPC, Subnets, S3, AZs |
| LakehouseCatalog | `6vtt2ycs570ezt` | AmazonSageMakerAdminIAMExecutionRole_1 | AmazonSageMakerAdminIAMExecutionRole_1 | `{}` vazio |
| DataLake | `6bbrztdwfxomeh` | AmazonSageMakerAdminIAMExecutionRole_1 | AmazonSageMakerAdminIAMExecutionRole_1 | `{}` vazio |
| RedshiftServerless | `5zux18nxyx6pd5` | AmazonSageMakerAdminIAMExecutionRole_1 | AmazonSageMakerAdminIAMExecutionRole_1 | `{}` vazio |

**Nota importante:** O template original cria 17 blueprints. O ambiente real tem apenas 4 habilitados. Os outros 13 blueprints existem no sistema (são "gerenciados pela AWS") mas não foram habilitados no domínio.

### 3.5 Blueprint Policy Grants

Cada blueprint habilitado precisa de uma policy grant que autoriza projetos a criarem ambientes daquele blueprint.

**Formato do entity_identifier:** `accountId:blueprintId` (descoberto empiricamente — o formato correto não está documentado explicitamente)

| Blueprint | Grant ID | Principal | Domain Unit | Include Children |
|-----------|----------|-----------|-------------|-----------------|
| Tooling | `00YUlM42rB` | CONTRIBUTOR | `6uns306w58f9yh` | `true` |
| LakehouseCatalog | `00cKlGQyRe` | CONTRIBUTOR | `6uns306w58f9yh` | `true` |
| DataLake | `00v9VbKIbz` | CONTRIBUTOR | `6uns306w58f9yh` | `true` |
| RedshiftServerless | `00EdTVs8mm` | CONTRIBUTOR | `6uns306w58f9yh` | `true` |

### 3.6 Project Profile "Default"

- **ID:** `dgfm4s2lizz44p`
- **Status:** `ENABLED`
- **Domain Unit:** `6uns306w58f9yh` (root)

**16 Environment Configurations:**

| # | Nome | Blueprint ID | Deploy Mode | Deploy Order | Params Principais |
|---|------|-------------|-------------|--------------|-------------------|
| 1 | Tooling | `3owsbi7jjppvc9` | ON_CREATE | 0 | enableSpaces=true, enableBedrockPermissions=true, enableNetworkIsolation=true, sagemakerDomainNetworkType=VpcOnly |
| 2 | Lakehouse Database | `6bbrztdwfxomeh` | ON_CREATE | 1 | glueDbName=glue_db |
| 3 | OnDemand Workflows | `b0eis75ozsqhd5` | ON_DEMAND | - | environmentClass=mw1.micro |
| 4 | OnDemand MLExperiments | `b78loa64t9oyuh` | ON_DEMAND | - | mlflowTrackingServerSize=Small |
| 5 | OnDemand EMR EC2 Memory | `atyconez9k8zjd` | ON_DEMAND | - | r6g.xlarge, emr-7.5.0 |
| 6 | OnDemand EMR EC2 General | `atyconez9k8zjd` | ON_DEMAND | - | m6g.xlarge, emr-7.5.0 |
| 7 | OnDemand RedshiftServerless | `5zux18nxyx6pd5` | ON_DEMAND | - | dbName=dev, baseCap=128 |
| 8 | OnDemand Catalog RMS | `6vtt2ycs570ezt` | ON_DEMAND | - | catalogDescription=RMS catalog |
| 9 | OnDemand EMRServerless | `c1vpqx2w5jxsh5` | ON_DEMAND | - | releaseLabel=emr-7.5.0 |
| 10 | Amazon Bedrock Chat Agent | `d55dwbwfj35qax` | ON_DEMAND | - | — |
| 11 | Amazon Bedrock Knowledge Base | `5smdhnwnnk8j55` | ON_DEMAND | - | — |
| 12 | Amazon Bedrock Guardrail | `4q5zrcfovzaq5l` | ON_DEMAND | - | — |
| 13 | Amazon Bedrock Function | `da33e9jk0oyq95` | ON_DEMAND | - | — |
| 14 | Amazon Bedrock Flow | `40xpt2w3xewr1l` | ON_DEMAND | - | — |
| 15 | Amazon Bedrock Prompt | `bx74dti0en1e95` | ON_DEMAND | - | — |
| 16 | Amazon Bedrock Evaluation | `6cxr3kg2f90uw9` | ON_DEMAND | - | — |

**ON_CREATE vs ON_DEMAND:**
- `ON_CREATE`: ambiente é criado **automaticamente** quando o projeto é criado. Os 2 primeiros (Tooling + Lakehouse Database) são criados em todos os projetos.
- `ON_DEMAND`: ambiente é criado apenas quando o usuário solicita explicitamente no console.

### 3.7 Project Profile Policy Grant

| Tipo | Grant ID | Principal | Domain Unit | Include Children | Profiles |
|------|----------|-----------|-------------|-----------------|----------|
| CREATE_PROJECT_FROM_PROJECT_PROFILE | `000TjLyvNt` | allUsersGrantFilter | `6uns306w58f9yh` | `true` | `dgfm4s2lizz44p` |

### 3.8 Domain Units (Subdomínios)

| ID | Projetos Associados | Nome Real |
|----|--------------------|-----------|
| `bv3pe06va5v0h5` | poc_catalogo_gov_dados_crm | **DESCONHECIDO** |
| `d35rdqcy3278yx` | poc_catalogo_gov_dados_fabrica_campanhas | **DESCONHECIDO** |

> ⚠️ O perfil `elo2` não tem permissão `datazone:GetDomainUnit` nem `datazone:ListDomainUnitsForParent`. Os nomes são desconhecidos. Os IDs são inferidos a partir dos campos `domainUnitId` nos projetos.

### 3.9 Projetos (4 existentes)

| Nome | ID | Domain Unit | Profile | logGroupRetention |
|------|----|-------------|---------|-------------------|
| `poc_catalogo_gov_dados` | `6rv1rrg6h1av55` | `6uns306w58f9yh` (root) | `dgfm4s2lizz44p` | 90 |
| `poc_catalogo_tableau` | `5tl8cx02xdc7c9` | `6uns306w58f9yh` (root) | `dgfm4s2lizz44p` | 1 |
| `poc_catalogo_gov_dados_crm` | `6ri81dg6zbvbc9` | `bv3pe06va5v0h5` (CRM) | `dgfm4s2lizz44p` | 731 |
| `poc_catalogo_gov_dados_fabrica_campanhas` | `bqdff5tckvrb1l` | `d35rdqcy3278yx` (Fábrica) | `dgfm4s2lizz44p` | 731 |

---

## 4. Comandos AWS CLI Utilizados

Todos os comandos usam `--profile elo2` e `--region us-east-2`.

### 4.1 Identificar a conta e o usuário atual

```bash
aws sts get-caller-identity --profile elo2
```

Saída relevante:
```json
{
  "UserId": "...",
  "Account": "679740497328",
  "Arn": "arn:aws:sts::679740497328:assumed-role/AWSReservedSSO_SSO-GovDados-Devs_.../gustavo.pereira.compass@elo.com.br"
}
```

### 4.2 Listar domínios DataZone

```bash
aws datazone list-domains \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

> ⚠️ O DataZone é regional. Se tentar em `us-east-1` (região padrão), pode receber `AccessDeniedException`.

Saída com os 3 domínios encontrados (poc-catalogo-gov-dados, Engenharia_de_dados, Default_02022026_Domain).

### 4.3 Obter detalhes do domínio

```bash
aws datazone get-domain \
  --identifier dzd-drrjoqtodsc8o9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna: ID, ARN, nome, versão, status SSO, roles de execução e serviço, root domain unit ID.

### 4.4 Listar projetos do domínio

```bash
aws datazone list-projects \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna: lista de projetos com ID, nome, `domainUnitId`, `projectStatus`, datas.

### 4.5 Obter detalhes de um projeto específico

```bash
aws datazone get-project \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --identifier 6ri81dg6zbvbc9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna: ID, nome, `domainUnitId`, `projectProfileId`, `userParameters` (parâmetros de cada ambiente do projeto).

### 4.6 Listar project profiles

```bash
aws datazone list-project-profiles \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

### 4.7 Obter detalhes completos do project profile

```bash
aws datazone get-project-profile \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --identifier dgfm4s2lizz44p \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna: todas as 16 `environmentConfigurations` com seus `parameterOverrides`.

### 4.8 Listar configurações de blueprint

```bash
aws datazone list-environment-blueprint-configurations \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna os 4 blueprints habilitados com suas roles e `regionalParameters`.

### 4.9 Obter nome de um blueprint pelo ID

```bash
aws datazone get-environment-blueprint \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --identifier 3owsbi7jjppvc9 \
  --region us-east-2 \
  --profile elo2 \
  --query '{name: name, description: description}' \
  --output json
```

### 4.10 Obter configuração de blueprint (uma específica)

```bash
aws datazone get-environment-blueprint-configuration \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --environment-blueprint-identifier 3owsbi7jjppvc9 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

### 4.11 Listar policy grants dos blueprints

```bash
# Formato correto: entity-identifier = "accountId:blueprintId"
aws datazone list-policy-grants \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --entity-type ENVIRONMENT_BLUEPRINT_CONFIGURATION \
  --entity-identifier "679740497328:3owsbi7jjppvc9" \
  --policy-type CREATE_ENVIRONMENT_FROM_BLUEPRINT \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

> 🔑 **Descoberta importante:** O `entity-identifier` para `ENVIRONMENT_BLUEPRINT_CONFIGURATION` usa o formato `accountId:blueprintId`. Tentar apenas o blueprint ID resulta em `ValidationException: Format of EnvironmentBlueprintConfigurationId is invalid`.

### 4.12 Listar policy grants do domain unit

```bash
aws datazone list-policy-grants \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --entity-type DOMAIN_UNIT \
  --entity-identifier 6uns306w58f9yh \
  --policy-type CREATE_PROJECT_FROM_PROJECT_PROFILE \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

### 4.13 Tentar listar domain units (bloqueado)

```bash
# Bloqueado — AccessDenied
aws datazone list-domain-units-for-parent \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --parent-domain-unit-identifier 6uns306w58f9yh \
  --region us-east-2 \
  --profile elo2 \
  --output json

# Bloqueado — AccessDenied
aws datazone get-domain-unit \
  --domain-identifier dzd-drrjoqtodsc8o9 \
  --identifier bv3pe06va5v0h5 \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

### 4.14 Listar domínios SageMaker (Studio clássico)

```bash
aws sagemaker list-domains \
  --region us-east-2 \
  --profile elo2 \
  --output json
```

Retorna os domínios do SageMaker Studio (cada projeto SMUS cria um domínio com nome `SageMakerUnifiedStudio-{project_id}-{sufixo}-dev`).

### 4.15 Script para listar grants de todos os blueprints de uma vez

```bash
for bp_id in 3owsbi7jjppvc9 6vtt2ycs570ezt 6bbrztdwfxomeh 5zux18nxyx6pd5; do
  echo "=== Blueprint $bp_id ==="
  aws datazone list-policy-grants \
    --domain-identifier dzd-drrjoqtodsc8o9 \
    --entity-type ENVIRONMENT_BLUEPRINT_CONFIGURATION \
    --entity-identifier "679740497328:${bp_id}" \
    --policy-type CREATE_ENVIRONMENT_FROM_BLUEPRINT \
    --region us-east-2 \
    --profile elo2 \
    --output json
done
```

### 4.16 Obter nome de múltiplos blueprints de uma vez

```bash
for bp_id in 3owsbi7jjppvc9 6vtt2ycs570ezt 6bbrztdwfxomeh 5zux18nxyx6pd5; do
  echo "=== Blueprint $bp_id ==="
  aws datazone get-environment-blueprint \
    --domain-identifier dzd-drrjoqtodsc8o9 \
    --identifier $bp_id \
    --region us-east-2 \
    --profile elo2 \
    --query '{name: name}' \
    --output json
done
```

### 4.17 Verificar o bucket S3 existente

```bash
aws s3api head-bucket \
  --bucket amazon-sagemaker-679740497328-us-east-2-00d422527895 \
  --region us-east-2 \
  --profile elo2
```

### 4.18 Verificar a role IAM ManageAccess

```bash
aws iam get-role \
  --role-name AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9 \
  --profile elo2
```

---

## 5. Análise do Template Oficial AWS

### 5.1 O que é o template?

O repositório contém uma cópia do template oficial AWS:
```
Unified-Studio-for-Amazon-Sagemaker/
└── terraform/
    ├── constructs/           ← módulos reutilizáveis
    │   ├── create-service-roles/
    │   ├── create-blueprint-roles/
    │   ├── create-blueprint/
    │   ├── create-blueprint-policy-grant/
    │   ├── create-project-profile-policy-grant/
    │   ├── create_project_profiles/
    │   └── create_project/
    └── examples/
        ├── single-account/   ← exemplo para uma conta
        └── multi-account/    ← exemplo para múltiplas contas
```

### 5.2 O que pode e o que não pode ser reutilizado

| Construto/Recurso | Reutilizável? | Motivo |
|-------------------|--------------|--------|
| `create-service-roles` | ❌ NÃO | Cria roles com nome aleatório (`DomainExecution{random}`). Real usa `AmazonSageMakerAdminIAMExecutionRole_1` |
| `awscc_datazone_domain` | ⚠️ PARCIAL | Estrutura sim, SSO precisa mudar para DISABLED |
| `aws_datazone_user_profile` | ❌ NÃO | SSO desabilitado — recurso inexistente no ambiente |
| `aws_s3_bucket` | ⚠️ PARCIAL | Estrutura sim, nome hardcoded (fórmula não funciona) |
| `create-blueprint-roles` | ⚠️ PARCIAL | ManageAccess: nome bate ✅. Provisioning: nome não bate ❌ |
| `create-blueprint` (17 bps) | ❌ NÃO | Template cria 17, real tem 4. Configs de roles diferem |
| `create-blueprint-policy-grant` | ✅ SIM | 100% reutilizável com `for_each` nos 4 blueprints |
| `create_project_profiles` | ❌ NÃO | Profile "Default" tem estrutura diferente dos perfis do template |
| `create-project-profile-policy-grant` | ✅ SIM | 95% compatível — mesma lógica `allUsersGrantFilter` |
| `create_project` | ❌ NÃO | Bug documentado no código + sem `domain_unit_id` |

### 5.3 Problema nos caminhos de módulos

O arquivo `main.tf` original na raiz do repositório tinha caminhos **incorretos**:
```hcl
# ❌ ERRADO — esse caminho não existe a partir da raiz
source = "../../constructs/create-service-roles"
```

Os caminhos corretos a partir da raiz são:
```hcl
# ✅ CORRETO
source = "Unified-Studio-for-Amazon-Sagemaker/terraform/constructs/create-blueprint-policy-grant"
```

---

## 6. Decisões de Implementação

### 6.1 Trabalhar na raiz do repositório

**Decisão:** Usar a raiz do repositório como diretório de trabalho Terraform, não criar um subdiretório.

**Motivo:** Simplicidade. O `terraform init` e `terraform apply` são executados diretamente na raiz. Os módulos são referenciados por caminho relativo a partir daí.

### 6.2 Data Sources para roles não gerenciadas

**Decisão:** Usar `data "aws_iam_role"` para as roles que o Terraform **não vai gerenciar**.

**Motivo:** A role `AmazonSageMakerAdminIAMExecutionRole_1` e `AmazonSageMakerProvisioning-679740497328` foram criadas antes do projeto Terraform e têm nome/configuração diferente do padrão do template. Se tentarmos importá-las via `resource`, qualquer drift na trust policy ou políticas anexadas causaria mudanças indesejadas.

### 6.3 Resource direto para ManageAccess (sem módulo)

**Decisão:** Declarar o recurso `aws_iam_role.sagemaker_manage_access` diretamente em `main.tf` em vez de usar o módulo `create-blueprint-roles`.

**Motivo:** O módulo criaria AMBAS as roles (ManageAccess + Provisioning). Como Provisioning não pode ser importada (nome difere), o módulo tentaria criar uma nova role Provisioning com nome errado. Ao declarar diretamente, temos controle total.

### 6.4 Blueprint configurations inline (sem módulo)

**Decisão:** Declarar os 4 `aws_datazone_environment_blueprint_configuration` diretamente em `main.tf`.

**Motivo:** O módulo `create-blueprint` cria 17 blueprints com a mesma configuração de roles para todos. No ambiente real, Tooling tem roles diferentes dos outros 3. Além disso, o módulo não oferece granularidade por blueprint.

### 6.5 Placeholder para nomes dos domain units

**Decisão:** Usar `name = "crm"` e `name = "fabrica_campanhas"` como placeholders.

**Motivo:** O perfil `elo2` não tem permissão `datazone:GetDomainUnit`. Os nomes reais são desconhecidos. Após o import, o `terraform plan` mostrará os nomes reais como "drift" e os placeholders poderão ser corrigidos.

---

## 7. Estrutura de Arquivos Terraform

```
poc-esteira-compass-repo/
├── providers.tf          # Configuração dos providers aws, awscc, time
├── variables.tf          # Declaração de variáveis
├── terraform.tfvars      # Valores reais das variáveis
├── main.tf               # Todos os recursos (606 linhas)
├── imports.tf            # Blocos de import para recursos existentes
└── Unified-Studio-for-Amazon-Sagemaker/
    └── terraform/
        └── constructs/
            ├── create-blueprint-policy-grant/   ← REUTILIZADO
            ├── create-project-profile-policy-grant/ ← REUTILIZADO
            ├── create-blueprint-roles/          ← NÃO USADO
            ├── create-service-roles/            ← NÃO USADO
            ├── create-blueprint/                ← NÃO USADO
            ├── create_project_profiles/         ← NÃO USADO
            └── create_project/                  ← NÃO USADO
```

---

## 8. Detalhamento de Cada Arquivo

### 8.1 `providers.tf`

```hcl
terraform {
  required_providers {
    aws   = { source = "hashicorp/aws",   version = ">= 6.19.0" }
    awscc = { source = "hashicorp/awscc", version = ">= 1.62.0" }
    time  = { source = "hashicorp/time",  version = ">= 0.9.0"  }
  }
}

provider "aws"   { region = "us-east-2", profile = "elo2" }
provider "awscc" { region = "us-east-2", profile = "elo2" }
```

**Por que o provider `time`?** O template original usa `resource "time_sleep"` para evitar race conditions. Mesmo que não estejamos usando no `main.tf` atual, é boa prática declarar o provider caso precise no futuro.

### 8.2 `variables.tf`

Define 5 variáveis:

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `domain_name` | `string` | Nome do domínio (default: "poc-catalogo-gov-dados") |
| `sagemaker_subnets` | `list(string)` | IDs das subnets da VPC |
| `sagemaker_vpc_id` | `string` | ID da VPC |
| `sagemaker_s3_bucket` | `string` | Nome do bucket S3 (sem prefixo s3://) |
| `sagemaker_azs` | `string` | AZs separadas por vírgula |

### 8.3 `terraform.tfvars`

Contém os valores reais:
```hcl
domain_name         = "poc-catalogo-gov-dados"
sagemaker_vpc_id    = "vpc-079d52c4150206c04"
sagemaker_subnets   = ["subnet-0374c7d945dfdbccd", "subnet-01ea650dbcbe8cdc5"]
sagemaker_s3_bucket = "amazon-sagemaker-679740497328-us-east-2-00d422527895"
sagemaker_azs       = "us-east-2b,us-east-2c"
```

### 8.4 `main.tf` — Estrutura em 10 seções

**Seção 1 — Data Sources:**
```hcl
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_iam_role" "domain_execution_role" { name = "AmazonSageMakerAdminIAMExecutionRole_1" }
data "aws_iam_role" "provisioning_role"     { name = "AmazonSageMakerProvisioning-679740497328" }
```

**Seção 2 — Domínio:**
- `awscc_datazone_domain.domain` com SSO DISABLED

**Seção 3 — S3 Bucket:**
- `aws_s3_bucket.dzs3_bucket` com nome hardcoded via variável

**Seção 4 — IAM ManageAccess:**
- `aws_iam_role.sagemaker_manage_access`
- `aws_iam_policy.sagemaker_manage_access_policy`
- 4x `aws_iam_role_policy_attachment`

**Seção 5 — Blueprint Configurations:**
- `aws_datazone_environment_blueprint_configuration.tooling`
- `aws_datazone_environment_blueprint_configuration.lakehouse_catalog`
- `aws_datazone_environment_blueprint_configuration.data_lake`
- `aws_datazone_environment_blueprint_configuration.redshift_serverless`

**Seção 6 — Blueprint Policy Grants (módulo):**
```hcl
module "blueprint_policy_grants" {
  source = "Unified-Studio-for-Amazon-Sagemaker/terraform/constructs/create-blueprint-policy-grant"
  blueprint_ids = tomap({ tooling_id = ..., lakehouse_catalog_id = ..., ... })
}
```

**Seção 7 — Project Profile "Default":**
- `awscc_datazone_project_profile.default_profile` com 16 `environment_configurations`

**Seção 8 — Project Profile Policy Grant (módulo):**
```hcl
module "project_profile_policy_grant" {
  source = "Unified-Studio-for-Amazon-Sagemaker/terraform/constructs/create-project-profile-policy-grant"
  project_profile_ids = [awscc_datazone_project_profile.default_profile.project_profile_id]
}
```

**Seção 9 — Domain Units:**
- `awscc_datazone_domain_unit.crm`
- `awscc_datazone_domain_unit.fabrica_campanhas`

**Seção 10 — Projetos:**
- `awscc_datazone_project.poc_catalogo_gov_dados`
- `awscc_datazone_project.poc_catalogo_tableau`
- `awscc_datazone_project.poc_catalogo_gov_dados_crm`
- `awscc_datazone_project.poc_catalogo_gov_dados_fabrica_campanhas`

### 8.5 `imports.tf` — Todos os 19 blocos de import

| Recurso Terraform | Import ID |
|-------------------|-----------|
| `awscc_datazone_domain.domain` | `dzd-drrjoqtodsc8o9` |
| `aws_s3_bucket.dzs3_bucket` | `amazon-sagemaker-679740497328-us-east-2-00d422527895` |
| `aws_iam_role.sagemaker_manage_access` | `AmazonSageMakerManageAccess-us-east-2-dzd-drrjoqtodsc8o9` |
| `aws_iam_policy.sagemaker_manage_access_policy` | `arn:aws:iam::679740497328:policy/service-role/AmazonSageMakerManageAccessPolicy-dzd-drrjoqtodsc8o9` |
| `aws_iam_role_policy_attachment.manage_access_glue` | `RoleName/PolicyArn` |
| `aws_iam_role_policy_attachment.manage_access_redshift` | `RoleName/PolicyArn` |
| `aws_iam_role_policy_attachment.manage_access_sagemaker` | `RoleName/PolicyArn` |
| `aws_iam_role_policy_attachment.manage_access_custom_policy` | `RoleName/PolicyArn` |
| `aws_datazone_environment_blueprint_configuration.tooling` | `dzd-drrjoqtodsc8o9/3owsbi7jjppvc9` |
| `aws_datazone_environment_blueprint_configuration.lakehouse_catalog` | `dzd-drrjoqtodsc8o9/6vtt2ycs570ezt` |
| `aws_datazone_environment_blueprint_configuration.data_lake` | `dzd-drrjoqtodsc8o9/6bbrztdwfxomeh` |
| `aws_datazone_environment_blueprint_configuration.redshift_serverless` | `dzd-drrjoqtodsc8o9/5zux18nxyx6pd5` |
| `module.blueprint_policy_grants.awscc_datazone_policy_grant.blueprint_policy_grants["tooling_id"]` | `dzd-drrjoqtodsc8o9\|679740497328:3owsbi7jjppvc9\|00YUlM42rB` |
| `module.blueprint_policy_grants.awscc_datazone_policy_grant.blueprint_policy_grants["lakehouse_catalog_id"]` | `dzd-drrjoqtodsc8o9\|679740497328:6vtt2ycs570ezt\|00cKlGQyRe` |
| `module.blueprint_policy_grants.awscc_datazone_policy_grant.blueprint_policy_grants["data_lake_id"]` | `dzd-drrjoqtodsc8o9\|679740497328:6bbrztdwfxomeh\|00v9VbKIbz` |
| `module.blueprint_policy_grants.awscc_datazone_policy_grant.blueprint_policy_grants["redshift_serverless_id"]` | `dzd-drrjoqtodsc8o9\|679740497328:5zux18nxyx6pd5\|00EdTVs8mm` |
| `awscc_datazone_project_profile.default_profile` | `dzd-drrjoqtodsc8o9\|dgfm4s2lizz44p` |
| `module.project_profile_policy_grant.awscc_datazone_policy_grant.project_profile_policy_grant` | `dzd-drrjoqtodsc8o9\|6uns306w58f9yh\|000TjLyvNt` |
| `awscc_datazone_domain_unit.crm` | `dzd-drrjoqtodsc8o9\|bv3pe06va5v0h5` |
| `awscc_datazone_domain_unit.fabrica_campanhas` | `dzd-drrjoqtodsc8o9\|d35rdqcy3278yx` |
| `awscc_datazone_project.poc_catalogo_gov_dados` | `dzd-drrjoqtodsc8o9\|6rv1rrg6h1av55` |
| `awscc_datazone_project.poc_catalogo_tableau` | `dzd-drrjoqtodsc8o9\|5tl8cx02xdc7c9` |
| `awscc_datazone_project.poc_catalogo_gov_dados_crm` | `dzd-drrjoqtodsc8o9\|6ri81dg6zbvbc9` |
| `awscc_datazone_project.poc_catalogo_gov_dados_fabrica_campanhas` | `dzd-drrjoqtodsc8o9\|bqdff5tckvrb1l` |

---

## 9. Recursos Terraform Mapeados

### Resumo de todos os recursos

```
Total de recursos gerenciados: ~24 recursos + módulos

aws_* (provider aws):
  ├── aws_s3_bucket.dzs3_bucket
  ├── aws_iam_role.sagemaker_manage_access
  ├── aws_iam_policy.sagemaker_manage_access_policy
  ├── aws_iam_role_policy_attachment.manage_access_glue
  ├── aws_iam_role_policy_attachment.manage_access_redshift
  ├── aws_iam_role_policy_attachment.manage_access_sagemaker
  ├── aws_iam_role_policy_attachment.manage_access_custom_policy
  ├── aws_datazone_environment_blueprint_configuration.tooling
  ├── aws_datazone_environment_blueprint_configuration.lakehouse_catalog
  ├── aws_datazone_environment_blueprint_configuration.data_lake
  └── aws_datazone_environment_blueprint_configuration.redshift_serverless

awscc_* (provider awscc):
  ├── awscc_datazone_domain.domain
  ├── awscc_datazone_project_profile.default_profile
  ├── awscc_datazone_domain_unit.crm
  ├── awscc_datazone_domain_unit.fabrica_campanhas
  ├── awscc_datazone_project.poc_catalogo_gov_dados
  ├── awscc_datazone_project.poc_catalogo_tableau
  ├── awscc_datazone_project.poc_catalogo_gov_dados_crm
  └── awscc_datazone_project.poc_catalogo_gov_dados_fabrica_campanhas

Módulos (via construtos do template):
  ├── module.blueprint_policy_grants
  │   └── awscc_datazone_policy_grant × 4 (um por blueprint)
  └── module.project_profile_policy_grant
      └── awscc_datazone_policy_grant × 1

Data Sources (não gerenciados):
  ├── data.aws_region.current
  ├── data.aws_caller_identity.current
  ├── data.aws_iam_role.domain_execution_role
  └── data.aws_iam_role.provisioning_role
```

---

## 10. Fluxo de Import — Como Funciona

### 10.1 Visão geral do processo

```
┌─────────────────────────────────────────────────────┐
│                     FLUXO COMPLETO                   │
└─────────────────────────────────────────────────────┘

  1. terraform init
     └─ Baixa providers aws, awscc, time
     └─ Inicializa módulos locais

  2. terraform plan  (com blocos import {} em imports.tf)
     └─ Para cada bloco import:
        └─ Lê o recurso REAL da AWS via API
        └─ Compara com o código em main.tf
        └─ Mostra o que está diferente (drifts)
     └─ Resultado: lista de mudanças necessárias

  3. Corrigir drifts em main.tf até que o plan mostre
     "0 to add, 0 to change, 0 to destroy"

  4. terraform apply
     └─ Importa todos os recursos para o state
     └─ Aplica qualquer mudança necessária
     └─ Cria terraform.tfstate com todos os recursos

  5. (Opcional) Configurar backend remoto
     └─ S3 + DynamoDB para state compartilhado
```

### 10.2 O que acontece durante o `terraform plan` com imports

Quando você executa `terraform plan` com blocos `import {}`, o Terraform:

1. **Lê o recurso real da AWS** usando as credenciais do provider
2. **Converte para estado interno** do Terraform
3. **Compara com o código HCL** em `main.tf`
4. **Mostra diferenças** — esses são os "drifts"

Exemplo de output esperado:
```
# awscc_datazone_domain_unit.crm will be imported
# (config will be regenerated)
  resource "awscc_datazone_domain_unit" "crm" {
    ~ name = "crm" -> "NomeRealDoDomainUnit"  ← DRIFT: nome errado
      id   = "bv3pe06va5v0h5"
    ...
  }
```

Você deve corrigir `name = "crm"` para `name = "NomeRealDoDomainUnit"` em `main.tf` e rodar o plan novamente até não haver mais drifts.

### 10.3 generate-config-out — Geração automática de HCL

Para recursos muito complexos (como o project profile com 16 configurações), o Terraform pode **gerar automaticamente o HCL** a partir do estado real:

```bash
terraform plan -generate-config-out=generated.tf
```

Isso cria um arquivo `generated.tf` com o código HCL exato que corresponde ao estado real. Você pode usar isso como referência para corrigir `main.tf`.

---

## 11. Próximos Passos

### Passo 1: Instalar o Terraform

```bash
# Verificar versão instalada
terraform version

# Versão mínima necessária: 1.5.0 (para import blocks nativos)
# Recomendado: >= 1.9.0
```

### Passo 2: Inicializar o Terraform

```bash
cd /home/gustavoliebl/VSCode/poc-esteira-compass-repo

terraform init
```

Saída esperada:
```
Initializing modules...
- blueprint_policy_grants in Unified-Studio-for-Amazon-Sagemaker/...
- project_profile_policy_grant in Unified-Studio-for-Amazon-Sagemaker/...

Initializing provider plugins...
- Finding hashicorp/aws versions matching ">= 6.19.0"...
- Finding hashicorp/awscc versions matching ">= 1.62.0"...
- Finding hashicorp/time versions matching ">= 0.9.0"...

Terraform has been successfully initialized!
```

### Passo 3: Executar o Plan

```bash
terraform plan -var-file=terraform.tfvars
```

Ou gerar o config automaticamente:
```bash
terraform plan -var-file=terraform.tfvars -generate-config-out=generated_config.tf
```

**O que observar no output:**
- Recursos com `will be imported` → os blocos import funcionaram
- `~ attribute` → drift a ser corrigido
- `+ resource` → recurso novo sendo criado (não deveria acontecer se tudo foi mapeado)
- `- resource` → recurso sendo destruído (PERIGO — verifique antes de aplicar)

### Passo 4: Corrigir Drifts Iterativamente

Os drifts mais prováveis de ocorrer:

1. **Nomes dos domain units** — os placeholders `"crm"` e `"fabrica_campanhas"` quase certamente estão errados:
   ```hcl
   # Em main.tf, seção 9, corrigir:
   resource "awscc_datazone_domain_unit" "crm" {
     name = "NOME_REAL_DO_DOMAIN_UNIT"  # ← corrigir aqui
   }
   ```

2. **Descrição do domínio** — pode estar diferente de `""`:
   ```hcl
   resource "awscc_datazone_domain" "domain" {
     description = "Descrição real se houver"  # ← corrigir se necessário
   }
   ```

3. **IAM Policy** — pode não existir se foi criada de forma diferente:
   - Se o plan mostrar que a policy não existe, remova o bloco import correspondente e o recurso `aws_iam_policy`
   - A policy pode ter nome diferente ou não existir

4. **Parâmetros do project profile** — o `generated_config.tf` mostrará os valores exatos

5. **`user_parameters` dos projetos** — pode precisar de ajuste nos parâmetros ou na estrutura

### Passo 5: Aplicar o Import

Depois de atingir `0 to add, 0 to change, 0 to destroy`:
```bash
terraform apply -var-file=terraform.tfvars
```

O Terraform importará todos os recursos para o state sem fazer mudanças na AWS.

### Passo 6: Verificar o State

```bash
# Listar todos os recursos no state
terraform state list

# Ver detalhes de um recurso específico
terraform state show awscc_datazone_domain.domain

# Ver o state completo
terraform show
```

### Passo 7: (Opcional) Configurar Backend Remoto

Para compartilhar o state com o time, configure um backend S3 com DynamoDB:

```hcl
# Adicionar em providers.tf:
terraform {
  backend "s3" {
    bucket         = "nome-do-bucket-de-state"
    key            = "poc-catalogo-gov-dados/terraform.tfstate"
    region         = "us-east-2"
    profile        = "elo2"
    dynamodb_table = "nome-da-tabela-de-lock"
    encrypt        = true
  }
  # ... required_providers ...
}
```

Depois:
```bash
terraform init -migrate-state
```

---

## 12. Informações Bloqueadas

O perfil `elo2` (SSO-GovDados-Devs) não tem as seguintes permissões IAM:

| Permissão Faltante | Impacto | Como Resolver |
|-------------------|---------|---------------|
| `datazone:GetDomainUnit` | Nomes reais dos domain units desconhecidos | Admin deve executar `aws datazone get-domain-unit --domain-identifier dzd-drrjoqtodsc8o9 --identifier bv3pe06va5v0h5 --region us-east-2` |
| `datazone:ListDomainUnitsForParent` | Não é possível listar todos os subdomínios | Idem acima |
| `datazone:ListProjectMemberships` | Membros dos projetos desconhecidos | Admin deve executar `aws datazone list-project-memberships --domain-identifier dzd-drrjoqtodsc8o9 --project-identifier 6rv1rrg6h1av55 --region us-east-2` |
| `iam:ListAttachedRolePolicies` | Políticas das roles desconhecidas | Admin deve verificar as 3 roles no console IAM |

### Checklist para o Administrador

Antes de executar o `terraform apply`, um administrador com permissões elevadas deve verificar:

- [ ] **Nome do Domain Unit CRM** (`bv3pe06va5v0h5`)
  ```bash
  aws datazone get-domain-unit \
    --domain-identifier dzd-drrjoqtodsc8o9 \
    --identifier bv3pe06va5v0h5 \
    --region us-east-2 \
    --profile <admin-profile>
  ```

- [ ] **Nome do Domain Unit Fábrica Campanhas** (`d35rdqcy3278yx`)
  ```bash
  aws datazone get-domain-unit \
    --domain-identifier dzd-drrjoqtodsc8o9 \
    --identifier d35rdqcy3278yx \
    --region us-east-2 \
    --profile <admin-profile>
  ```

- [ ] **Políticas da role ManageAccess** — verificar se a IAM Policy customizada existe:
  ```bash
  aws iam get-policy \
    --policy-arn arn:aws:iam::679740497328:policy/service-role/AmazonSageMakerManageAccessPolicy-dzd-drrjoqtodsc8o9 \
    --profile <admin-profile>
  ```

---

## 13. Referência Rápida de IDs

### Domínio e unidades

```
Domain ID:         dzd-drrjoqtodsc8o9
Root Domain Unit:  6uns306w58f9yh
Domain Unit CRM:   bv3pe06va5v0h5
Domain Unit Fábr:  d35rdqcy3278yx
```

### Blueprints habilitados

```
Tooling:            3owsbi7jjppvc9
LakehouseCatalog:   6vtt2ycs570ezt
DataLake:           6bbrztdwfxomeh
RedshiftServerless: 5zux18nxyx6pd5
```

### Blueprints ON_DEMAND (no project profile, não habilitados no domínio)

```
Workflows (MWAA):       b0eis75ozsqhd5
MLExperiments:          b78loa64t9oyuh
EMR on EC2:             atyconez9k8zjd
EMR Serverless:         c1vpqx2w5jxsh5
Bedrock Chat Agent:     d55dwbwfj35qax
Bedrock Knowledge Base: 5smdhnwnnk8j55
Bedrock Guardrail:      4q5zrcfovzaq5l
Bedrock Function:       da33e9jk0oyq95
Bedrock Flow:           40xpt2w3xewr1l
Bedrock Prompt:         bx74dti0en1e95
Bedrock Evaluation:     6cxr3kg2f90uw9
```

### Policy Grants

```
Blueprint Tooling grant:           00YUlM42rB
Blueprint LakehouseCatalog grant:  00cKlGQyRe
Blueprint DataLake grant:          00v9VbKIbz
Blueprint RedshiftServerless grant: 00EdTVs8mm
Project Profile grant:             000TjLyvNt
```

### Project Profile e Projetos

```
Default Profile ID:                 dgfm4s2lizz44p

poc_catalogo_gov_dados:             6rv1rrg6h1av55  (root)
poc_catalogo_tableau:               5tl8cx02xdc7c9  (root)
poc_catalogo_gov_dados_crm:         6ri81dg6zbvbc9  (CRM)
poc_catalogo_gov_dados_fabrica_:    bqdff5tckvrb1l  (Fábrica)
```

---

## 14. Troubleshooting

### Problema: `Error: Invalid provider configuration`

```
Error: Invalid provider configuration
│ Provider "registry.terraform.io/hashicorp/awscc" requires explicit configuration.
```

**Solução:** Verifique se o provider `awscc` está configurado em `providers.tf` com `region` e `profile`.

### Problema: `Error: Module not installed`

```
Error: Module not installed
│ module.blueprint_policy_grants is not installed
```

**Solução:** Execute `terraform init` novamente.

### Problema: `ValidationException: Format of EnvironmentBlueprintConfigurationId is invalid`

Ao chamar `list-policy-grants` com `entity-type ENVIRONMENT_BLUEPRINT_CONFIGURATION`.

**Solução:** O entity_identifier deve ser no formato `accountId:blueprintId`, não apenas o blueprint ID:
```bash
--entity-identifier "679740497328:3owsbi7jjppvc9"
```

### Problema: `AccessDeniedException` ao listar domain units

```
AccessDeniedException: User ... is not authorized to perform: datazone:ListDomainUnitsForParent
```

**Solução:** O perfil `elo2` não tem esta permissão. Use um perfil com permissões de administrador ou solicite ao administrador que forneça os nomes dos domain units.

### Problema: Import falha com `Resource not found`

```
Error: Cannot import non-existent remote object
```

**Causa provável:** O ID de import está errado.

**Verificação:**
```bash
# Para awscc resources, verificar se o ID no formato correto
# awscc usa | como separador
# aws usa / como separador
```

### Problema: Plan mostra `~ single_sign_on` mudanças

Se o plan mostrar que o `single_sign_on` precisa ser alterado, pode ser que o provider awscc espere um formato diferente para SSO DISABLED. Tente:
```hcl
# Opção 1: omitir completamente o bloco single_sign_on
resource "awscc_datazone_domain" "domain" {
  # sem single_sign_on
}

# Opção 2: manter como está
single_sign_on = {
  type            = "DISABLED"
  user_assignment = "MANUAL"
}
```

### Problema: Plan mostra destruição de resources

```
- resource "awscc_datazone_project" ... will be destroyed
```

**PERIGO!** Nunca aplique um plan que destrói recursos existentes sem entender por quê.

Causas comuns:
- O recurso está duplicado no código
- O import block está apontando para o recurso errado
- O recurso não foi encontrado na AWS (ID errado)

**Solução:** Use `terraform plan -out=plan.tfplan && terraform show plan.tfplan` para revisar detalhadamente antes de aplicar.

---

*Documentação gerada em 18/02/2026. Para dúvidas ou atualizações, consulte os arquivos de memória em `.claude/projects/.../memory/`.*
