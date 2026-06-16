# Modulo SageMaker Studio

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Modos de Rede](#modos-de-rede)
- [Auto-Shutdown de Apps Ociosos](#auto-shutdown-de-apps-ociosos)
- [Integracao MLflow](#integracao-mlflow)
- [Uso](#uso)
  - [Uso Basico](#uso-basico)
  - [Uso Completo](#uso-completo)
  - [Uso com VPC Mode](#uso-com-vpc-mode)
- [Variaveis](#variaveis)
  - [Identificacao](#identificacao)
  - [Rede](#rede)
  - [Acesso S3](#acesso-s3)
  - [Integracao MLflow](#integracao-mlflow-1)
  - [Tipos de Instancia](#tipos-de-instancia)
  - [Seguranca](#seguranca)
  - [CloudWatch Logs](#cloudwatch-logs)
  - [Idle Shutdown](#idle-shutdown)
  - [User Profiles](#user-profiles)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)
- [Custos Estimados](#custos-estimados)
- [Limitacoes SSO](#limitacoes-sso)
- [Decisoes de Arquitetura](#decisoes-de-arquitetura)
- [Referencias](#referencias)

---

## Visao Geral

| Item | Descricao |
|------|-----------|
| **Proposito** | Criar ambiente de desenvolvimento integrado (IDE) para Data Scientists |
| **Provider** | AWS SageMaker |
| **Tipo** | SageMaker Studio Domain |
| **Auth Mode** | IAM |
| **Network Modes** | PublicInternetOnly ou VpcOnly |

### Caracteristicas Principais

| Caracteristica | Descricao |
|----------------|-----------|
| **IDE Gerenciado** | JupyterLab, CodeEditor (VS Code-like) e Terminal |
| **Auto-Shutdown** | Desligamento automatico de apps ociosos (Set/2024) |
| **Integracao MLflow** | Suporte a MLflow Tracking Server via variavel de configuracao |
| **User Profiles** | Criacao automatica de perfis de usuario |
| **Criptografia** | Suporte a KMS para EBS, EFS e S3 |
| **CloudWatch Logs** | Logs centralizados das sessoes do Studio |

---

## Arquitetura

### SageMaker Studio Ecosystem

```
+-----------------------------------------------------------------------------+
|                        SAGEMAKER STUDIO ECOSYSTEM                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|   AWS CONSOLE / CLI                                                         |
|         |                                                                   |
|         | IAM Auth                                                          |
|         v                                                                   |
|   +-------------------------------------------------------------------+     |
|   |                    SAGEMAKER STUDIO DOMAIN                        |     |
|   |                                                                   |     |
|   |   +---------------------+  +---------------------+                |     |
|   |   |    USER PROFILE     |  |    USER PROFILE     |                |     |
|   |   |    (data-scientist) |  |    (ml-engineer)    |                |     |
|   |   +----------+----------+  +----------+----------+                |     |
|   |              |                        |                           |     |
|   |              +------------+-----------+                           |     |
|   |                           |                                       |     |
|   |   +-----------------------v-----------------------+               |     |
|   |   |                   APPS                        |               |     |
|   |   |                                               |               |     |
|   |   |   +-----------+  +-----------+  +-----------+ |               |     |
|   |   |   |JupyterLab |  |CodeEditor |  | Terminal  | |               |     |
|   |   |   |   App     |  |   App     |  |   App     | |               |     |
|   |   |   | (system)  |  | (system)  |  | (system)  | |               |     |
|   |   |   +-----------+  +-----------+  +-----------+ |               |     |
|   |   |                                               |               |     |
|   |   |   +-----------------------------------------+ |               |     |
|   |   |   |           KERNEL GATEWAY                | |               |     |
|   |   |   |         (ml.t3.medium)                  | |               |     |
|   |   |   |   - Python 3                            | |               |     |
|   |   |   |   - Data Science packages               | |               |     |
|   |   |   +-----------------------------------------+ |               |     |
|   |   |                                               |               |     |
|   |   +-----------------------------------------------+               |     |
|   |                           |                                       |     |
|   |   +-----------------------v-----------------------+               |     |
|   |   |                STORAGE (EFS)                  |               |     |
|   |   |   /home/sagemaker-user/                       |               |     |
|   |   |   - notebooks/                                |               |     |
|   |   |   - data/                                     |               |     |
|   |   +-----------------------------------------------+               |     |
|   |                                                                   |     |
|   +-------------------------------------------------------------------+     |
|                                   |                                         |
|                                   | IAM Execution Role                      |
|                                   v                                         |
|   +-------------------------------------------------------------------+     |
|   |                       INTEGRACOES                                 |     |
|   |                                                                   |     |
|   |   +--------+  +--------+  +--------+  +--------+  +--------+      |     |
|   |   |   S3   |  | MLflow |  |SageMaker|  |Bedrock |  |CodeCommit    |     |
|   |   |Buckets |  | Server |  |Training |  | Models |  |   Repos |    |     |
|   |   +--------+  +--------+  +--------+  +--------+  +--------+      |     |
|   |                                                                   |     |
|   +-------------------------------------------------------------------+     |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Fluxo de Trabalho do Data Scientist

```
+-----------------------------------------------------------------------------+
|                     CICLO DE DESENVOLVIMENTO ML                             |
+-----------------------------------------------------------------------------+
|                                                                             |
|   1. EXPLORACAO              2. DESENVOLVIMENTO           3. TREINAMENTO    |
|   +--------------+          +-----------------+          +---------------+  |
|   |              |          |                 |          |               |  |
|   | Carregar     |          | Feature         |          | SageMaker     |  |
|   | dados S3     |--------->| Engineering     |--------->| Training Job  |  |
|   | (JupyterLab) |          | em Notebook     |          |               |  |
|   |              |          |                 |          |               |  |
|   +--------------+          +-----------------+          +-------+-------+  |
|         ^                                                        |          |
|         |                                                        v          |
|   6. MONITORAMENTO          5. DEPLOY                  4. REGISTRO          |
|   +--------------+          +-----------------+          +---------------+  |
|   |              |          |                 |          |               |  |
|   | CloudWatch   |          | SageMaker       |          | MLflow        |  |
|   | Metricas     |<---------| Endpoint        |<---------| Model         |  |
|   |              |          | (Inferencia)    |          | Registry      |  |
|   |              |          |                 |          |               |  |
|   +--------------+          +-----------------+          +---------------+  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Diagrama de Rede (VPC Mode)

```
                                    Internet
                                        |
                                        | (Bloqueado)
                                        |
+---------------------------------------+---------------------------------------+
|                                      VPC                                      |
|                                                                               |
|   +---------------------------+       +---------------------------+           |
|   |    PRIVATE SUBNET AZ-A   |       |    PRIVATE SUBNET AZ-B   |           |
|   |                          |       |                          |           |
|   |   +------------------+   |       |   +------------------+   |           |
|   |   | SageMaker Studio |   |       |   | SageMaker Studio |   |           |
|   |   |    Domain        |   |       |   |    (HA)          |   |           |
|   |   +--------+---------+   |       |   +--------+---------+   |           |
|   |            |             |       |            |             |           |
|   +------------|-------------+       +------------|-------------+           |
|                |                                  |                         |
|                +----------------------------------+                         |
|                                |                                            |
|                    +-----------v-----------+                                |
|                    |    Security Group     |                                |
|                    |  - Egress HTTPS (443) |                                |
|                    |  - Egress NFS (2049)  |                                |
|                    |  - Ingress self       |                                |
|                    +-----------+-----------+                                |
|                                |                                            |
|        +-----------------------+------------------------+                   |
|        |                       |                        |                   |
|        v                       v                        v                   |
|   +----------+           +----------+             +----------+              |
|   | S3 VPC   |           | EFS VPC  |             | SageMaker|              |
|   | Endpoint |           | Endpoint |             | Endpoint |              |
|   +----------+           +----------+             +----------+              |
|                                                                               |
+-------------------------------------------------------------------------------+
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `aws_sagemaker_domain.main` | Domain | SageMaker Studio Domain |
| `aws_iam_role.execution` | IAM Role | Execution Role para notebooks e jobs |
| `aws_iam_role_policy_attachment.*` | Policy Attachments | Permissoes AWS Managed |
| `aws_cloudwatch_log_group.studio` | Log Group | Logs das sessoes do Studio |
| `aws_security_group.studio` | Security Group | Regras de rede (VPC mode) |
| `aws_sagemaker_user_profile.users` | User Profiles | Perfis de usuario |

### IAM Policies Anexadas

| Policy | Tipo | Descricao |
|--------|------|-----------|
| `AmazonSageMakerFullAccess` | AWS Managed | Acesso completo ao SageMaker |
| `AmazonS3FullAccess` | AWS Managed | Acesso completo ao S3 |
| `CloudWatchLogsFullAccess` | AWS Managed | Acesso completo a logs |
| `AWSCodeCommitPowerUser` | AWS Managed | Git operations no CodeCommit |
| `AmazonBedrockFullAccess` | AWS Managed | Chamar modelos Bedrock |

---

## Modos de Rede

### Comparativo

| Modo | Acesso Internet | Seguranca | Uso Recomendado |
|------|-----------------|-----------|-----------------|
| **PublicInternetOnly** | Sim | Basica | Desenvolvimento rapido, POC |
| **VpcOnly** | Nao (via NAT/VPC Endpoints) | Alta | Producao, compliance |

### PublicInternetOnly

```
Usuario --> Internet --> SageMaker Studio --> AWS Services
```

- **Vantagens**: Facil configuracao, sem dependencias de VPC
- **Desvantagens**: Trafego via internet publica
- **Quando usar**: Desenvolvimento, experimentacao, POC

### VpcOnly

```
Usuario --> VPN --> VPC --> SageMaker Studio --> VPC Endpoints --> AWS Services
```

- **Vantagens**: Trafego interno, maior seguranca
- **Desvantagens**: Requer VPC Endpoints, configuracao mais complexa
- **Quando usar**: Producao, dados sensiveis, compliance

---

## Auto-Shutdown de Apps Ociosos

> **Recurso nativo AWS lancado em Setembro/2024**

### Configuracao

| Parametro | Descricao | Obrigatorio | Range |
|-----------|-----------|-------------|-------|
| `idle_timeout_in_minutes` | Tempo de inatividade antes de desligar apps | Sim | 60-525600 |

> **Nota**: O modulo configura automaticamente `min_idle_timeout` e `max_idle_timeout` com o mesmo valor de `idle_timeout_in_minutes`.

### Apps Suportados

| App | Auto-Shutdown | Observacao |
|-----|---------------|------------|
| JupyterLab | Sim | Requer SageMaker Distribution v2.0+ |
| CodeEditor | Sim | VS Code-like |
| Terminal | Nao | Nao suportado |
| Kernel Gateway | Nao | Gerenciado separadamente |

### Beneficios

- **Reducao de custos**: Apps desligados nao consomem recursos
- **Preservacao de dados**: EFS mantem arquivos salvos
- **Transparencia**: Usuario notificado antes do shutdown
- **Configuravel**: Usuarios podem ajustar timeout (dentro dos limites)

---

## Integracao MLflow

### Configuracao Manual

Para integrar com MLflow Tracking Server, configure a variavel `mlflow_tracking_server_name`.

A Execution Role criada pelo modulo inclui `AmazonSageMakerFullAccess`, que contem permissoes `sagemaker-mlflow:*` necessarias para operacoes MLflow.

### Tracking URI

Dentro do notebook, configure o tracking URI:

```python
import mlflow

# Formato do tracking URI
mlflow.set_tracking_uri("aws://sagemaker/{mlflow_tracking_server_name}")

# Exemplo
mlflow.set_tracking_uri("aws://sagemaker/elo-fraud-mlflow-dev")
```

### Variaveis de Ambiente

Para persistir a configuracao, adicione ao ambiente:

```bash
export MLFLOW_TRACKING_URI="aws://sagemaker/{mlflow_tracking_server_name}"
```

---

## Uso

### Uso Basico

```hcl
module "sagemaker_studio" {
  source = "./modules/sagemaker-studio"

  # Identificacao
  project_name        = "elo-fraud"
  environment         = "dev"
  domain_name         = "elo-fraud-studio-dev"
  execution_role_name = "elo-fraud-studio-dev-execution-role"
  log_group_name      = "/aws/sagemaker/studio/elo-fraud-studio-dev"

  # VPC (obrigatorio mesmo para PublicInternetOnly)
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  # Idle Shutdown
  idle_timeout_in_minutes = 60
}

# Acessar Studio via console ou CLI
output "studio_domain_id" {
  value = module.sagemaker_studio.domain_id
}
```

### Uso Completo

```hcl
module "sagemaker_studio" {
  source = "./modules/sagemaker-studio"

  # Identificacao
  project_name        = "elo-fraud"
  environment         = "prod"
  domain_name         = "elo-fraud-studio-prod"
  execution_role_name = "elo-fraud-studio-prod-execution-role"
  log_group_name      = "/aws/sagemaker/studio/elo-fraud-studio-prod"

  # Rede (PublicInternetOnly)
  enable_vpc_mode = false
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids

  # Acesso S3
  s3_bucket_arns = [
    module.s3.raw_bucket_arn,
    module.s3.processed_bucket_arn,
    module.s3.models_bucket_arn
  ]

  # Integracao MLflow
  mlflow_tracking_server_name = module.mlflow.tracking_server_name

  # Tipos de Instancia
  default_notebook_instance_type = "ml.t3.medium"

  # Seguranca
  kms_key_id = aws_kms_key.sagemaker.arn

  # CloudWatch Logs
  log_retention_days = 30

  # Idle Shutdown (economia de custos)
  idle_timeout_in_minutes = 60

  # User Profiles (opcional)
  user_profiles = [
    {
      name               = "data-scientist-1"
      execution_role_arn = null  # Usa role padrao
    },
    {
      name               = "ml-engineer-1"
      execution_role_arn = aws_iam_role.ml_engineer.arn  # Role customizada
    }
  ]

  # Tags
  tags = {
    Project     = "elo-fraud"
    Environment = "prod"
    Team        = "data-science"
    CostCenter  = "ml-platform"
  }
}

# Outputs
output "studio_info" {
  value = {
    domain_id          = module.sagemaker_studio.domain_id
    domain_url         = module.sagemaker_studio.domain_url
    execution_role_arn = module.sagemaker_studio.execution_role_arn
  }
}
```

### Uso com VPC Mode

```hcl
module "sagemaker_studio" {
  source = "./modules/sagemaker-studio"

  # Identificacao
  project_name        = "elo-fraud"
  environment         = "prod"
  domain_name         = "elo-fraud-studio-prod"
  execution_role_name = "elo-fraud-studio-prod-execution-role"
  log_group_name      = "/aws/sagemaker/studio/elo-fraud-studio-prod"

  # Rede - VPC Mode (mais seguro)
  enable_vpc_mode = true
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids  # Minimo 1 subnet

  # Integracao MLflow
  mlflow_tracking_server_name = module.mlflow.tracking_server_name

  # Idle Shutdown
  idle_timeout_in_minutes = 60

  tags = {
    Environment = "prod"
    Compliance  = "required"
  }
}

# IMPORTANTE: VPC Mode requer VPC Endpoints para:
# - S3 (Gateway Endpoint)
# - SageMaker API (Interface Endpoint)
# - SageMaker Runtime (Interface Endpoint)
# - CloudWatch Logs (Interface Endpoint)
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `project_name` | `string` | Sim | - | Nome do projeto |
| `environment` | `string` | Sim | - | Ambiente (dev, staging, prod) |
| `domain_name` | `string` | Sim | - | Nome do SageMaker Studio Domain |
| `execution_role_name` | `string` | Sim | - | Nome da IAM Execution Role para o Studio |
| `log_group_name` | `string` | Sim | - | Nome do CloudWatch Log Group |
| `tags` | `map(string)` | Nao | `{}` | Tags adicionais |

### Rede

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `enable_vpc_mode` | `bool` | Nao | `false` | Habilitar VpcOnly mode |
| `vpc_id` | `string` | Condicional | `null` | ID da VPC |
| `subnet_ids` | `list(string)` | Condicional | `[]` | IDs das subnets privadas |

### Acesso S3

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `s3_bucket_arns` | `list(string)` | Nao | `[]` | ARNs de buckets S3 |

### Integracao MLflow

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `mlflow_tracking_server_name` | `string` | Nao | `null` | Nome do MLflow Tracking Server |

### Tipos de Instancia

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `default_notebook_instance_type` | `string` | Nao | `ml.t3.medium` | Instance type padrao para notebooks |

### Seguranca

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `kms_key_id` | `string` | Nao | `null` | ARN da KMS key para criptografia |

### CloudWatch Logs

| Variavel | Tipo | Obrigatorio | Default | Validacao | Descricao |
|----------|------|-------------|---------|-----------|-----------|
| `log_retention_days` | `number` | Nao | `7` | Valores CloudWatch | Dias de retencao de logs |

### Idle Shutdown

| Variavel | Tipo | Obrigatorio | Default | Validacao | Descricao |
|----------|------|-------------|---------|-----------|-----------|
| `idle_timeout_in_minutes` | `number` | Sim | - | 60-525600 | Tempo de inatividade antes de desligar apps |

### User Profiles

| Variavel | Tipo | Obrigatorio | Default | Descricao |
|----------|------|-------------|---------|-----------|
| `user_profiles` | `list(object)` | Nao | `[]` | Lista de user profiles a criar |

**Estrutura do objeto user_profile:**
```hcl
{
  name               = string        # Nome do user profile
  execution_role_arn = optional(string)  # ARN da role (null = usar padrao)
}
```

---

## Outputs

### Domain

| Output | Tipo | Descricao |
|--------|------|-----------|
| `domain_id` | `string` | ID do SageMaker Studio Domain |
| `domain_arn` | `string` | ARN do Domain |
| `domain_name` | `string` | Nome do Domain |
| `domain_url` | `string` | URL base do Studio |
| `home_efs_file_system_id` | `string` | ID do EFS para home directories |

### IAM

| Output | Tipo | Descricao |
|--------|------|-----------|
| `execution_role_arn` | `string` | ARN da Execution Role |
| `execution_role_name` | `string` | Nome da Execution Role |

### Security Group

| Output | Tipo | Descricao |
|--------|------|-----------|
| `security_group_id` | `string` | ID do Security Group (null se PublicInternetOnly) |

### CloudWatch

| Output | Tipo | Descricao |
|--------|------|-----------|
| `log_group_name` | `string` | Nome do Log Group |
| `log_group_arn` | `string` | ARN do Log Group |

### Idle Shutdown

| Output | Tipo | Descricao |
|--------|------|-----------|
| `idle_timeout_in_minutes` | `number` | Tempo de ociosidade antes de desligar apps (minutos) |

### Agregados

| Output | Tipo | Descricao |
|--------|------|-----------|
| `studio_connection_info` | `object` | Todas as informacoes de conexao |
| `usage_instructions` | `string` | Instrucoes de uso formatadas |
| `user_profiles` | `map(object)` | Mapa de user profiles criados |
| `user_profile_arns` | `list(string)` | Lista de ARNs dos user profiles |

---

## Operacoes

### Acessar SageMaker Studio

```bash
# Via AWS Console
# 1. AWS Console → SageMaker → Domains
# 2. Selecionar o domain
# 3. Clicar no user profile → "Launch" → "Studio"

# Via AWS CLI - Criar user profile
aws sagemaker create-user-profile \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario \
  --region sa-east-1

# Via AWS CLI - Gerar URL de acesso
aws sagemaker create-presigned-domain-url \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario \
  --region sa-east-1
```

### Gerenciar User Profiles

```bash
# Listar user profiles
aws sagemaker list-user-profiles \
  --domain-id d-xxxxxxxxxx \
  --output table

# Descrever user profile
aws sagemaker describe-user-profile \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario

# Deletar user profile
aws sagemaker delete-user-profile \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario
```

### Gerenciar Apps

```bash
# Listar apps de um user profile
aws sagemaker list-apps \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name-equals meu-usuario \
  --output table

# Deletar app (forcar shutdown)
aws sagemaker delete-app \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario \
  --app-type JupyterServer \
  --app-name default
```

### Verificar Lifecycle Config (se existir)

```bash
# Listar lifecycle configs (criados manualmente ou por outros modulos)
aws sagemaker list-studio-lifecycle-configs \
  --output table

# Descrever lifecycle config especifico
aws sagemaker describe-studio-lifecycle-config \
  --studio-lifecycle-config-name <nome-do-lifecycle-config>
```

### Ver Logs do Studio

```bash
# Listar log streams
aws logs describe-log-streams \
  --log-group-name /aws/sagemaker/studio/elo-fraud-studio-dev \
  --order-by LastEventTime \
  --descending

# Ver logs em tempo real
aws logs tail /aws/sagemaker/studio/elo-fraud-studio-dev --follow

# Filtrar logs por padrao
aws logs filter-log-events \
  --log-group-name /aws/sagemaker/studio/elo-fraud-studio-dev \
  --filter-pattern "ERROR"
```

### Verificar Idle Shutdown

```bash
# Descrever domain para ver configuracoes
aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query "DefaultUserSettings.JupyterLabAppSettings.AppLifecycleManagement" \
  --output json
```

---

## Troubleshooting

### User Profile nao Consegue Acessar Studio

**Sintoma**: Erro ao tentar abrir Studio

**Diagnostico**:
```bash
# Verificar status do user profile
aws sagemaker describe-user-profile \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name meu-usuario

# Verificar apps
aws sagemaker list-apps \
  --domain-id d-xxxxxxxxxx \
  --user-profile-name-equals meu-usuario
```

**Causas Comuns**:
1. App em estado `Failed` ou `Deleting`
2. Execution Role sem permissoes
3. Subnet sem conectividade (VPC mode)

**Solucoes**:
- Deletar app com erro e recriar
- Verificar IAM policies da execution role
- Verificar VPC Endpoints (VPC mode)

### MLflow nao Conecta

**Sintoma**: `MLFLOW_TRACKING_URI` nao configurado

**Diagnostico**:
```python
# Dentro do notebook
import os
print(os.getenv('MLFLOW_TRACKING_URI'))
```

**Causas Comuns**:
1. Variavel de ambiente nao configurada
2. MLflow tracking server nao existe
3. Permissoes insuficientes

**Solucoes**:
```bash
# Configurar variavel de ambiente
export MLFLOW_TRACKING_URI="aws://sagemaker/{server-name}"
```

```python
# Ou configurar diretamente no notebook
import mlflow
mlflow.set_tracking_uri("aws://sagemaker/{server-name}")
```

### App nao Desliga Automaticamente

**Sintoma**: Apps continuam rodando apos periodo de inatividade

**Diagnostico**:
```bash
# Verificar configuracao
aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query "DefaultUserSettings.JupyterLabAppSettings.AppLifecycleManagement"
```

**Causas Comuns**:
1. SageMaker Distribution antiga (< v2.0)
2. Extensao de monitoramento ausente
3. Timeout configurado muito alto

**Solucoes**:
- Atualizar para SageMaker Distribution v2.0+
- Verificar `jupyter-activity-monitor-extension >= 0.3.1`
- Ajustar `idle_timeout_in_minutes` para valor menor (minimo 60)

### Erro: Access Denied ao S3

**Sintoma**: Notebook nao consegue ler/escrever no S3

**Diagnostico**:
```bash
# Verificar role
aws sagemaker describe-domain \
  --domain-id d-xxxxxxxxxx \
  --query "DefaultUserSettings.ExecutionRole"

# Verificar policies
aws iam list-attached-role-policies \
  --role-name elo-fraud-studio-dev-execution-role
```

**Solucoes**:
- Verificar se `AmazonS3FullAccess` esta anexada
- Verificar bucket policies que bloqueiam acesso

---

## Custos Estimados

### Componentes de Custo

| Componente | Cobranca | Observacao |
|------------|----------|------------|
| Studio Domain | Gratuito | Apenas criacao |
| JupyterServer App | Gratuito | App de orquestracao |
| Kernel Gateway (ml.t3.medium) | ~$0.05/hora | Por hora de uso |
| Kernel Gateway (ml.m5.xlarge) | ~$0.23/hora | Para cargas maiores |
| EFS Storage | ~$0.30/GB/mes | Home directories |
| CloudWatch Logs | ~$0.50/GB | Logs ingeridos |

### Estimativa Mensal

| Cenario | Uso | Custo Estimado |
|---------|-----|----------------|
| DEV (1 DS, 4h/dia) | 80h ml.t3.medium | ~$4/mes |
| DEV (1 DS, 8h/dia, sem auto-shutdown) | 240h ml.t3.medium | ~$12/mes |
| PROD (5 DS, 6h/dia) | 600h ml.t3.medium | ~$30/mes |
| PROD (5 DS, treinamento) | 100h ml.m5.xlarge | ~$23/mes |

### Economia com Idle Shutdown

| Cenario | Sem Auto-Shutdown | Com Auto-Shutdown (60min) | Economia |
|---------|-------------------|---------------------------|----------|
| 1 DS, 8h trabalho | 720h/mes | ~180h/mes | **75%** |
| 5 DS, 6h trabalho | 3600h/mes | ~900h/mes | **75%** |

---

## Limitacoes SSO

> **IMPORTANTE**: Algumas policies IAM customizadas estao comentadas devido a limitacoes de permissoes SSO.

### Recursos Comentados

| Recurso | Acao Bloqueada | Mitigacao |
|---------|----------------|-----------|
| `aws_iam_policy.mlflow_access` | `iam:CreatePolicy` | Usar `AmazonSageMakerFullAccess` (inclui sagemaker-mlflow:*) |
| `aws_iam_policy.s3_access` | `iam:CreatePolicy` | Usar `AmazonS3FullAccess` |
| `aws_iam_policy.cloudwatch` | `iam:CreatePolicy` | Usar `CloudWatchLogsFullAccess` |
| `aws_iam_role.execution` (tags) | `iam:TagRole` | Tags ignoradas via lifecycle |

### Impacto

- Policies AWS Managed sao mais permissivas que custom policies
- Para ambientes com requisitos de seguranca rigorosos, criar policies manualmente

---

## Decisoes de Arquitetura

### Por que IAM Auth Mode?

| Decisao | IAM Authentication |
|---------|-------------------|
| **Motivo** | Simplifica autenticacao usando credenciais AWS existentes |
| **Beneficio** | Nao requer IdP externo, integra com SSO AWS |
| **Trade-off** | Menos flexibilidade que SSO com SAML |
| **Alternativa** | SSO Mode (requer configuracao de IdP) |

### Por que PublicInternetOnly em Dev?

| Decisao | PublicInternetOnly para Desenvolvimento |
|---------|----------------------------------------|
| **Motivo** | Facilita acesso sem configuracao de VPN/VPC Endpoints |
| **Beneficio** | Setup rapido, menos dependencias |
| **Trade-off** | Trafego via internet publica |
| **Quando mudar** | Ambientes de producao ou com dados sensiveis |

### Por que ml.t3.medium como Default?

| Decisao | ml.t3.medium |
|---------|--------------|
| **Motivo** | Recursos suficientes para exploracao inicial |
| **Beneficio** | Custo baixo (~$0.05/hora) |
| **Trade-off** | Pode ser lento para datasets grandes |
| **Quando mudar** | Treinamento pesado → ml.m5.xlarge ou maior |

### Por que Idle Shutdown de 60 minutos?

| Decisao | 60 minutos (minimo AWS) |
|---------|-------------------------|
| **Motivo** | Balanco entre produtividade e economia |
| **Beneficio** | Reduz custos em ate 75% |
| **Trade-off** | Usuario pode perder sessao se ausentar |
| **Mitigacao** | Dados salvos no EFS sao preservados |

### Por que AWS Managed Policies?

| Decisao | Usar AWS Managed Policies |
|---------|---------------------------|
| **Motivo** | Limitacoes de SSO (iam:CreatePolicy bloqueado) |
| **Beneficio** | Deploy funciona sem permissoes especiais |
| **Trade-off** | Policies mais permissivas que necessario |
| **Mitigacao** | Seguranca adicional via bucket policies e SCPs |

---

## Referencias

### AWS Documentation

- [Amazon SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/studio.html)
- [SageMaker Studio Lifecycle Configurations](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-lcc.html)
- [SageMaker Studio Idle Shutdown](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-idle-shutdown.html)
- [SageMaker MLflow Integration](https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html)
- [SageMaker Domain VPC](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-vpc.html)

### Terraform Documentation

- [aws_sagemaker_domain](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_domain)
- [aws_sagemaker_user_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_user_profile)
- [aws_sagemaker_studio_lifecycle_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_studio_lifecycle_config)

### Best Practices

- [SageMaker Studio Best Practices](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-best-practices.html)
- [SageMaker Security](https://docs.aws.amazon.com/sagemaker/latest/dg/security.html)
- [MLflow on AWS](https://mlflow.org/docs/latest/tracking.html#amazon-sagemaker)
