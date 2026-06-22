# IAM Policies - MLOps Modules Implementation

**Data**: 2026-02-18
**Autor**: Gustavo Liebl Pereira
**Branch**: `gustaavolp-compasso`
**Conta AWS**: `888577064416` (single account, multi-region)

---

## 1. Contexto e Motivacao

A analise comparativa entre os ambientes DEV (us-east-1) e STAGING (sa-east-1) revelou que o ambiente DEV possuia **9 IAM policies adicionais** aplicadas manualmente (via Console/CLI) em 2 IAM Roles da stack MLOps. Essas policies nao estavam codificadas no Terraform, gerando:

- **Drift de configuracao**: DEV e STAGING com permissoes diferentes
- **Falta de rastreabilidade**: alteracoes manuais sem historico no Git
- **Risco operacional**: recriar o ambiente perderia essas policies

As 2 roles afetadas:

| Role | Modulo Terraform |
|------|-----------------|
| `elo-fraud-studio-{env}-execution-role` | `infra/modules/sagemaker-studio` |
| `elo-fraud-mlflow-{env}-execution-role` | `infra/modules/mlflow` |

---

## 2. O que Foi Feito

### 2.1. Modulo `sagemaker-studio/main.tf` — 4 policies adicionadas

**Arquivo**: `infra/modules/sagemaker-studio/main.tf`
**Role**: `elo-fraud-studio-{env}-execution-role`

Policies existentes (ja estavam no Terraform):

| # | Resource Terraform | Policy ARN |
|---|-------------------|------------|
| 1 | `sagemaker_full_access` | `AmazonSageMakerFullAccess` |
| 2 | `s3_full_access` | `AmazonS3FullAccess` |
| 3 | `cloudwatch_logs_full_access` | `CloudWatchLogsFullAccess` |
| 4 | `codecommit_power_user` | `AWSCodeCommitPowerUser` |
| 5 | `bedrock_full_access` | `AmazonBedrockFullAccess` |

**Policies adicionadas nesta alteracao**:

| # | Resource Terraform | Policy ARN | Tipo | Motivo |
|---|-------------------|------------|------|--------|
| 6 | `sqs_full_access` | `arn:aws:iam::aws:policy/AmazonSQSFullAccess` | Managed | Acesso SQS para notebooks |
| 7 | `dynamodb_full_access` | `arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess` | Managed | Acesso DynamoDB (feature store) |
| 8 | `canvas_data_science_assistant` | `arn:aws:iam::aws:policy/AmazonSageMakerCanvasSMDataScienceAssistantAccess` | Managed | Canvas Data Science Assistant |
| 9 | `studio_project_ml_policy` | `arn:aws:iam::aws:policy/SageMakerStudioProjectRoleMachineLearningPolicy` | Managed | Projetos ML no Studio |

**Total apos alteracao**: 9 managed policy attachments na role Studio.

### 2.2. Modulo `mlflow/main.tf` — 4 policies managed + 1 inline adicionadas

**Arquivo**: `infra/modules/mlflow/main.tf`
**Role**: `elo-fraud-mlflow-{env}-execution-role`

Policies existentes (ja estavam no Terraform):

| # | Resource Terraform | Policy ARN |
|---|-------------------|------------|
| 1 | `sagemaker_full_access` | `AmazonSageMakerFullAccess` |
| 2 | `s3_full_access` | `AmazonS3FullAccess` |
| 3 | `cloudwatch_logs_full_access` | `CloudWatchLogsFullAccess` |
| 4 | `firehose_full_access` | `AmazonKinesisFirehoseFullAccess` |
| 5 | `bedrock_full_access` | `AmazonBedrockFullAccess` |

**Policies adicionadas nesta alteracao**:

| # | Resource Terraform | Policy ARN / Nome | Tipo | Motivo |
|---|-------------------|-------------------|------|--------|
| 6 | `sqs_full_access` | `arn:aws:iam::aws:policy/AmazonSQSFullAccess` | Managed | Acesso SQS |
| 7 | `codecommit_power_user` | `arn:aws:iam::aws:policy/AWSCodeCommitPowerUser` | Managed | Git no Studio (user profile usa esta role) |
| 8 | `dynamodb_full_access` | `arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess` | Managed | Acesso DynamoDB |
| 9 | `studio_project_ml_policy` | `arn:aws:iam::aws:policy/SageMakerStudioProjectRoleMachineLearningPolicy` | Managed | Projetos ML |
| 10 | `sagemaker_mlflow_full_access` | `SageMakerMLflowFullAccess` (inline) | Inline | `sagemaker-mlflow:*` para MLflow SDK |

**Total apos alteracao**: 9 managed policy attachments + 1 inline policy na role MLflow.

### 2.3. Copia para `compra-online-repo`

Os mesmos 2 arquivos foram copiados identicamente para o repositorio CodeCommit:

- `compra-online-repo/infra/modules/sagemaker-studio/main.tf`
- `compra-online-repo/infra/modules/mlflow/main.tf`

### 2.4. Validacao Local

| Verificacao | Resultado |
|-------------|-----------|
| `terraform fmt -check` nos 2 modulos | PASS |
| Diff entre repos (elocartoes vs compra-online) | Identicos |
| Contagem de resources de policy por modulo | 12 cada (correto) |

---

## 3. Arquivos Modificados

| Arquivo | Alteracao | Linhas Adicionadas |
|---------|-----------|-------------------|
| `infra/modules/sagemaker-studio/main.tf` | +4 `aws_iam_role_policy_attachment` | ~40 linhas |
| `infra/modules/mlflow/main.tf` | +4 `aws_iam_role_policy_attachment` + 1 `aws_iam_role_policy` (inline) | ~60 linhas |

**Nenhum arquivo de environment foi alterado** (`terraform.tfvars`, `variables.tf`, `main.tf` dos envs).
Os modulos sao compartilhados — a alteracao se propaga automaticamente para todos os ambientes.

---

## 4. Analise de Impacto

### 4.1. Seguranca

- **Sem alteracao destrutiva**: Apenas `aws_iam_role_policy_attachment` e `aws_iam_role_policy` (operacoes idempotentes)
- **Sem alteracao em**: Domain, User Profiles, EFS, Security Groups, S3 Buckets, Tracking Server
- **Policies sao AWS Managed**: Mantidas pela AWS, sem risco de definicao incorreta
- **Inline policy**: Escopo limitado a `sagemaker-mlflow:*` (somente MLflow SDK)

### 4.2. Comportamento por Ambiente

| Ambiente | Regiao | Comportamento Esperado |
|----------|--------|----------------------|
| **DEV** | us-east-1 | Policies ja existem na AWS (aplicadas manualmente). O Terraform **adota** no state sem criar/alterar nada na AWS. |
| **STAGING** | sa-east-1 | Policies **serao criadas** pela primeira vez. Novos resources no state e na AWS. |

### 4.3. Relacao User Profile e MLflow Role

**Ponto critico**: Em ambos os ambientes, o User Profile do SageMaker Studio (`elo-fraud-ml-user`) usa a **execution role do MLflow** (nao a do Studio):

```hcl
# infra/environments/{env}/mlops/main.tf
user_profiles = [
  {
    name               = "elo-fraud-ml-user"
    execution_role_arn = module.mlflow.execution_role_arn  # <-- MLflow role
  }
]
```

Isso significa que quando um usuario abre o Studio, ele usa a role `elo-fraud-mlflow-{env}-execution-role`. Por isso as policies de CodeCommit, DynamoDB, SQS e ML Projects foram adicionadas tambem na role do MLflow.

### 4.4. Diferenca de Rede entre Ambientes

| Config | DEV | STAGING |
|--------|-----|---------|
| `app_network_access_type` | `PublicInternetOnly` | `VpcOnly` |
| Subnets | Publicas | Privadas |
| Security Group Studio | Nao criado | Criado (com regras NFS, HTTPS, DNS) |
| `vpc_cidr` passada | Nao | Sim |

> **Nota**: Esta diferenca de rede **nao afeta** as alteracoes de IAM. As policies sao aplicadas na role independente do modo de rede.

---

## 5. Resultado Esperado no Terraform Plan

### 5.1. STAGING (`sa-east-1`) — Stack MLOps

```
Plan: 9 to add, 0 to change, 0 to destroy.
```

Novos resources esperados:

```
module.sagemaker_studio.aws_iam_role_policy_attachment.sqs_full_access
module.sagemaker_studio.aws_iam_role_policy_attachment.dynamodb_full_access
module.sagemaker_studio.aws_iam_role_policy_attachment.canvas_data_science_assistant
module.sagemaker_studio.aws_iam_role_policy_attachment.studio_project_ml_policy
module.mlflow.aws_iam_role_policy_attachment.sqs_full_access
module.mlflow.aws_iam_role_policy_attachment.codecommit_power_user
module.mlflow.aws_iam_role_policy_attachment.dynamodb_full_access
module.mlflow.aws_iam_role_policy_attachment.studio_project_ml_policy
module.mlflow.aws_iam_role_policy.sagemaker_mlflow_full_access
```

### 5.2. DEV (`us-east-1`) — Stack MLOps

```
Plan: 9 to add, 0 to change, 0 to destroy.
```

Mesmos 9 resources. Na AWS as policies ja existem — o Terraform vai **criar os bindings no state** e verificar que o estado real ja corresponde ao desejado.

> **Atencao**: Se alguma policy foi removida manualmente de DEV entre a analise e o apply, o Terraform ira recria-la.

---

## 6. Proximos Passos — Implementacao em DEV

### Pre-requisitos

- Terraform v1.14.x instalado localmente
- AWS CLI configurado com credenciais da conta `888577064416`
- Profile com permissao `iam:AttachRolePolicy` e `iam:PutRolePolicy`
- Acesso ao bucket de state: `elo-fraud-terraform-state-888577064416-us-east-1`

### Passo 1: Configurar credenciais AWS para DEV

```bash
# Verificar que esta na conta correta
aws sts get-caller-identity
# Esperado: Account = 888577064416

# Verificar regiao
aws configure get region
# Deve ser: us-east-1 (ou configurar via export)
export AWS_DEFAULT_REGION=us-east-1
```

### Passo 2: Navegar ate a stack MLOps DEV

```bash
cd infra/environments/dev/mlops
```

### Passo 3: Inicializar o Terraform

```bash
terraform init
```

Saida esperada:
```
Initializing the backend...
Initializing modules...
Terraform has been successfully initialized!
```

> **Nota**: Se os modulos ja estavam inicializados, pode ser necessario `terraform init -upgrade` para capturar as mudancas no modulo local.

### Passo 4: Validar a configuracao

```bash
terraform validate
```

Saida esperada:
```
Success! The configuration is valid.
```

### Passo 5: Executar o Plan

```bash
terraform plan -out=plan-dev-mlops.tfplan
```

**Verificar CUIDADOSAMENTE**:

1. O plan deve mostrar **exatamente 9 resources to add**
2. **0 resources to change**
3. **0 resources to destroy**
4. Os 9 resources devem ser APENAS `aws_iam_role_policy_attachment` e `aws_iam_role_policy`
5. **Nenhum** recurso de Domain, User Profile, Tracking Server, S3, EFS deve aparecer

Se o plan mostrar **qualquer destroy ou change** em recursos existentes, **NAO prossiga**. Investigue a causa.

### Passo 6: Revisar o Plan detalhado

```bash
terraform show plan-dev-mlops.tfplan
```

Confirmar que cada resource mostra:

- `role` = nome correto da role
- `policy_arn` = ARN correto da AWS Managed Policy
- Para a inline policy: `policy` contendo `sagemaker-mlflow:*`

### Passo 7: Aplicar (com aprovacao manual)

```bash
terraform apply plan-dev-mlops.tfplan
```

Saida esperada:
```
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.
```

### Passo 8: Verificar via AWS CLI

```bash
# Policies na role Studio
aws iam list-attached-role-policies \
  --role-name elo-fraud-studio-dev-execution-role \
  --query 'AttachedPolicies[].PolicyName' \
  --output table

# Policies na role MLflow (managed)
aws iam list-attached-role-policies \
  --role-name elo-fraud-mlflow-dev-execution-role \
  --query 'AttachedPolicies[].PolicyName' \
  --output table

# Policies na role MLflow (inline)
aws iam list-role-policies \
  --role-name elo-fraud-mlflow-dev-execution-role \
  --output table
```

**Resultado esperado para Studio (9 policies)**:

| PolicyName |
|------------|
| AmazonSageMakerFullAccess |
| AmazonS3FullAccess |
| CloudWatchLogsFullAccess |
| AWSCodeCommitPowerUser |
| AmazonBedrockFullAccess |
| AmazonSQSFullAccess |
| AmazonDynamoDBFullAccess |
| AmazonSageMakerCanvasSMDataScienceAssistantAccess |
| SageMakerStudioProjectRoleMachineLearningPolicy |

**Resultado esperado para MLflow (9 managed + 1 inline)**:

Managed:

| PolicyName |
|------------|
| AmazonSageMakerFullAccess |
| AmazonS3FullAccess |
| CloudWatchLogsFullAccess |
| AmazonKinesisFirehoseFullAccess |
| AmazonBedrockFullAccess |
| AmazonSQSFullAccess |
| AWSCodeCommitPowerUser |
| AmazonDynamoDBFullAccess |
| SageMakerStudioProjectRoleMachineLearningPolicy |

Inline:

| PolicyName |
|------------|
| SageMakerMLflowFullAccess |

---

## 7. Proximos Passos — Implementacao em STAGING

### Passo 1: Configurar credenciais AWS para STAGING

```bash
aws sts get-caller-identity
# Esperado: Account = 888577064416

export AWS_DEFAULT_REGION=sa-east-1
```

### Passo 2: Navegar ate a stack MLOps STAGING

```bash
cd infra/environments/staging/mlops
```

### Passo 3: Inicializar o Terraform

```bash
terraform init
```

> **Nota**: O backend do state esta em `us-east-1` mesmo para staging. O `terraform init` precisa de acesso a `us-east-1` para o bucket S3.

### Passo 4: Validar

```bash
terraform validate
```

### Passo 5: Plan

```bash
terraform plan -out=plan-staging-mlops.tfplan
```

**Mesmas verificacoes do DEV** (Passo 5 e 6 acima).

### Passo 6: Apply

```bash
terraform apply plan-staging-mlops.tfplan
```

### Passo 7: Verificar via AWS CLI

```bash
# Policies na role Studio (staging)
aws iam list-attached-role-policies \
  --role-name elo-fraud-studio-staging-execution-role \
  --query 'AttachedPolicies[].PolicyName' \
  --output table

# Policies na role MLflow (staging - managed)
aws iam list-attached-role-policies \
  --role-name elo-fraud-mlflow-staging-execution-role \
  --query 'AttachedPolicies[].PolicyName' \
  --output table

# Policies na role MLflow (staging - inline)
aws iam list-role-policies \
  --role-name elo-fraud-mlflow-staging-execution-role \
  --output table
```

---

## 8. Ordem de Execucao Recomendada

| Etapa | Ambiente | Acao | Motivo |
|-------|----------|------|--------|
| 1 | DEV | `terraform plan` | Validar que o plan mostra apenas adds (policies ja existem) |
| 2 | DEV | `terraform apply` | Adotar policies existentes no state (menor risco) |
| 3 | DEV | Verificar AWS CLI | Confirmar paridade |
| 4 | DEV | Testar Studio/MLflow | Abrir notebook, rodar mlflow.set_tracking_uri() |
| 5 | STAGING | `terraform plan` | Validar plan (policies serao criadas) |
| 6 | STAGING | `terraform apply` | Criar policies novas |
| 7 | STAGING | Verificar AWS CLI | Confirmar paridade com DEV |
| 8 | STAGING | Testar Studio/MLflow | Mesmo teste funcional |

> **Recomendacao**: Executar DEV primeiro porque as policies ja existem la. Se o plan mostrar algo inesperado, e mais seguro investigar sem risco de criar policies incorretas em STAGING.

---

## 9. Rollback (se necessario)

As alteracoes sao **facilmente reversiveis**:

### Reverter no Terraform

1. Remover os blocos adicionados de `main.tf` (ambos os modulos)
2. Executar `terraform plan` — mostrara "9 to destroy" (apenas policy attachments)
3. Executar `terraform apply`

### Reverter manualmente na AWS

```bash
# Exemplo: remover uma policy de uma role
aws iam detach-role-policy \
  --role-name elo-fraud-studio-dev-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess

# Remover inline policy
aws iam delete-role-policy \
  --role-name elo-fraud-mlflow-dev-execution-role \
  --policy-name SageMakerMLflowFullAccess
```

> **Nota**: Reverter policy attachments NAO afeta o SageMaker Domain, User Profiles, MLflow Tracking Server ou qualquer outro recurso. Apenas as permissoes da role sao alteradas.

---

## 10. Troubleshooting

### Erro: `iam:AttachRolePolicy` Access Denied

A conta possui SCPs que limitam operacoes IAM. Se receber este erro:

1. Verificar se a policy existe: `aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess`
2. Verificar se o SCP permite `iam:AttachRolePolicy` para managed policies
3. Se bloqueado, solicitar excecao ao time de seguranca

### Erro: `iam:PutRolePolicy` Access Denied (inline policy)

O SCP pode bloquear `iam:PutRolePolicy`. Se isso acontecer:

1. Verificar se ha excecao para roles com prefixo `elo-fraud-`
2. Alternativa: criar a policy como managed policy customizada (requer `iam:CreatePolicy`, tambem pode ser bloqueada)

### Terraform mostra changes inesperados no Domain/User Profile

Se alem dos 9 adds o plan mostrar changes em `aws_sagemaker_domain` ou `aws_sagemaker_user_profile`:

1. **NAO aplique** sem investigar
2. Pode ser drift em outro atributo (ex: idle_timeout alterado manualmente)
3. Verificar com `terraform state show module.sagemaker_studio.aws_sagemaker_domain.main`
4. Se necessario, usar `terraform plan -target=module.mlflow.aws_iam_role_policy_attachment.sqs_full_access` para aplicar policies individualmente

### Como aplicar policies individualmente (target)

Se quiser aplicar uma por uma para maior controle:

```bash
# Exemplo: aplicar apenas a policy SQS na role Studio
terraform apply -target=module.sagemaker_studio.aws_iam_role_policy_attachment.sqs_full_access

# Todos os targets disponiveis:
# module.sagemaker_studio.aws_iam_role_policy_attachment.sqs_full_access
# module.sagemaker_studio.aws_iam_role_policy_attachment.dynamodb_full_access
# module.sagemaker_studio.aws_iam_role_policy_attachment.canvas_data_science_assistant
# module.sagemaker_studio.aws_iam_role_policy_attachment.studio_project_ml_policy
# module.mlflow.aws_iam_role_policy_attachment.sqs_full_access
# module.mlflow.aws_iam_role_policy_attachment.codecommit_power_user
# module.mlflow.aws_iam_role_policy_attachment.dynamodb_full_access
# module.mlflow.aws_iam_role_policy_attachment.studio_project_ml_policy
# module.mlflow.aws_iam_role_policy.sagemaker_mlflow_full_access
```

---

## 11. Configuracao dos Backends (Referencia)

Ambos os ambientes usam o **mesmo bucket S3** para state (em `us-east-1`):

| Ambiente | State Key | Regiao do Backend |
|----------|-----------|------------------|
| DEV | `dev/mlops/terraform.tfstate` | us-east-1 |
| STAGING | `staging/mlops/terraform.tfstate` | us-east-1 |

**Bucket**: `elo-fraud-terraform-state-888577064416-us-east-1`
**Locking**: Native (`use_lockfile = true`, sem DynamoDB)
**Terraform**: `~> 1.14.0`
**AWS Provider**: `~> 6.0`

---

## 12. Inventario Final de Policies por Role

### Role: `elo-fraud-studio-{env}-execution-role`

| # | Policy | Tipo | Origem |
|---|--------|------|--------|
| 1 | AmazonSageMakerFullAccess | Managed | Original |
| 2 | AmazonS3FullAccess | Managed | Original |
| 3 | CloudWatchLogsFullAccess | Managed | Original |
| 4 | AWSCodeCommitPowerUser | Managed | Original |
| 5 | AmazonBedrockFullAccess | Managed | Original |
| 6 | AmazonSQSFullAccess | Managed | **Novo** |
| 7 | AmazonDynamoDBFullAccess | Managed | **Novo** |
| 8 | AmazonSageMakerCanvasSMDataScienceAssistantAccess | Managed | **Novo** |
| 9 | SageMakerStudioProjectRoleMachineLearningPolicy | Managed | **Novo** |

### Role: `elo-fraud-mlflow-{env}-execution-role`

| # | Policy | Tipo | Origem |
|---|--------|------|--------|
| 1 | AmazonSageMakerFullAccess | Managed | Original |
| 2 | AmazonS3FullAccess | Managed | Original |
| 3 | CloudWatchLogsFullAccess | Managed | Original |
| 4 | AmazonKinesisFirehoseFullAccess | Managed | Original |
| 5 | AmazonBedrockFullAccess | Managed | Original |
| 6 | AmazonSQSFullAccess | Managed | **Novo** |
| 7 | AWSCodeCommitPowerUser | Managed | **Novo** |
| 8 | AmazonDynamoDBFullAccess | Managed | **Novo** |
| 9 | SageMakerStudioProjectRoleMachineLearningPolicy | Managed | **Novo** |
| 10 | SageMakerMLflowFullAccess (sagemaker-mlflow:*) | **Inline** | **Novo** |
