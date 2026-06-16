# MLOps Stack - DEV

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Provisionados](#recursos-provisionados)
- [Pre-requisitos](#pre-requisitos)
- [Guia de Implantacao](#guia-de-implantacao)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Guia de Uso](#guia-de-uso)
- [Integracao com Outras Stacks](#integracao-com-outras-stacks)
- [Custos Estimados](#custos-estimados)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

A **MLOps Stack** provisiona as ferramentas de Machine Learning Operations para experimentacao, rastreamento e gerenciamento do ciclo de vida de modelos ML. Esta stack e independente da aplicacao principal, permitindo atualizacoes e experimentacoes sem impactar o sistema de deteccao de fraude.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Experiment Tracking** | Rastreamento de experimentos, parametros e metricas |
| **Model Registry** | Registro e versionamento de modelos treinados |
| **Artifact Storage** | Armazenamento de artefatos de treinamento |
| **Development Environment** | IDE gerenciada para desenvolvimento de modelos |

### Por que uma Stack Separada?

| Beneficio | Descricao |
|-----------|-----------|
| **Isolamento** | Mudancas em MLOps nao afetam a aplicacao de fraude |
| **Resiliencia** | Erros de deploy nao impactam Foundation ou Platform |
| **Ciclo Independente** | MLflow e Studio podem ser atualizados separadamente |
| **Experimentacao** | Ambiente seguro para testar novas versoes |

---

## Arquitetura

```
                              AWS Region: us-east-1
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            MLOps Stack                                      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     MLflow Tracking Server                          │   │
│   │                     (SageMaker Managed)                             │   │
│   │                                                                     │   │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐   │   │
│   │   │  Tracking       │    │  Artifact       │    │  CloudWatch   │   │   │
│   │   │  Server         │    │  Bucket (S3)    │    │  Log Group    │   │   │
│   │   │  (Small)        │    │                 │    │               │   │   │
│   │   │                 │    │  90 dias        │    │  7 dias       │   │   │
│   │   │  MLflow 3.0     │    │  retention      │    │  retention    │   │   │
│   │   └─────────────────┘    └─────────────────┘    └───────────────┘   │   │
│   │                                                                     │   │
│   │   Features:                                                         │   │
│   │   - Automatic Model Registration                                    │   │
│   │   - Weekly Maintenance (Sun 03:00)                                  │   │
│   │   - IAM Role with Full Permissions                                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     SageMaker Studio Domain                         │   │
│   │                                                                     │   │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐   │   │
│   │   │  Studio         │    │  User Profile   │    │  Lifecycle    │   │   │
│   │   │  Domain         │    │                 │    │  Config       │   │   │
│   │   │                 │    │  elo-fraud-     │    │               │   │   │
│   │   │  PublicInternet │    │  ml-user        │    │  MLflow       │   │   │
│   │   │  Only           │    │                 │    │  Integration  │   │   │
│   │   └─────────────────┘    └─────────────────┘    └───────────────┘   │   │
│   │                                                                     │   │
│   │   Features:                                                         │   │
│   │   - ml.t3.medium Default Instance                                   │   │
│   │   - Idle Shutdown (60 min)                                          │   │
│   │   - Access to Foundation S3 Buckets                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Consome via remote_state
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Foundation Stack                                   │
│                                                                             │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│   │     VPC       │  │    Subnets    │  │  S3 Buckets   │                  │
│   │               │  │    (public)   │  │  raw/proc/    │                  │
│   │               │  │               │  │  models       │                  │
│   └───────────────┘  └───────────────┘  └───────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Trabalho ML

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Data Scientist │────▶│ SageMaker Studio│────▶│  MLflow Server  │
│                 │     │                 │     │                 │
│  - Desenvolve   │     │  - Notebooks    │     │  - Log metrics  │
│  - Experimenta  │     │  - Training     │     │  - Log params   │
│  - Treina       │     │  - Debugging    │     │  - Log models   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Model Registry │◀────│ Artifact Bucket │
                        │                 │     │      (S3)       │
                        │  - Versioning   │     │                 │
                        │  - Staging      │     │  - Artifacts    │
                        │  - Production   │     │  - Checkpoints  │
                        └─────────────────┘     └─────────────────┘
```

---

## Recursos Provisionados

### MLflow Tracking Server

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-mlflow-dev |
| **Tamanho** | Small |
| **Versao** | 3.0 |
| **Model Registration** | Automatico |
| **Janela de Manutencao** | Domingos 03:00 UTC |

#### Componentes Criados

| Componente | Descricao |
|------------|-----------|
| **Tracking Server** | Servidor MLflow gerenciado pela AWS |
| **Artifact Bucket** | S3 bucket dedicado para artefatos |
| **IAM Role** | Role com permissoes SageMaker e S3 |
| **CloudWatch Log Group** | Logs do servidor (7 dias retencao) |

#### Configuracoes do Artifact Bucket

| Configuracao | Valor |
|--------------|-------|
| **Versionamento** | Habilitado |
| **Criptografia** | AES256 (SSE-S3) |
| **Lifecycle** | Habilitado |
| **Retencao** | 90 dias |

### SageMaker Studio Domain

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-studio-dev |
| **Modo de Rede** | PublicInternetOnly |
| **Instancia Padrao** | ml.t3.medium |
| **Idle Shutdown** | 60 minutos |

#### User Profiles

| Profile | Descricao |
|---------|-----------|
| **elo-fraud-ml-user** | Perfil padrao para cientistas de dados |

#### Acesso a Buckets S3

| Bucket | Permissao |
|--------|-----------|
| raw | Leitura |
| processed | Leitura/Escrita |
| models | Leitura/Escrita |
| mlflow-artifacts | Leitura/Escrita |

---

## Pre-requisitos

### Dependencias

| Requisito | Descricao |
|-----------|-----------|
| **Bootstrap** | Stack de bootstrap aplicada |
| **Foundation** | Stack foundation aplicada (VPC, S3) |
| **Terraform** | >= 1.10.0 |
| **AWS Provider** | ~> 5.0 |

### Permissoes AWS Necessarias

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:*",
        "s3:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
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
# 1. Certifique-se que Foundation foi aplicada
cd infra/environments/dev/foundation
terraform output vpc_id  # Deve retornar um VPC ID

# 2. Navegue ate o diretorio MLOps
cd ../mlops

# 3. Inicialize o Terraform
terraform init

# 4. Visualize as mudancas
terraform plan

# 5. Aplique a infraestrutura
terraform apply

# 6. Verifique os outputs
terraform output
```

### Verificacao Pos-Implantacao

```bash
# Verificar MLflow Tracking Server
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev \
  --region us-east-1

# Verificar SageMaker Studio Domain
aws sagemaker list-domains --region us-east-1

# Verificar bucket de artifacts
aws s3 ls | grep mlflow

# Obter URL do MLflow UI
terraform output mlflow_tracking_server_url
```

---

## Estrutura de Arquivos

```
infra/environments/dev/mlops/
├── main.tf              # Recursos principais (MLflow, Studio)
├── variables.tf         # Definicao de variaveis
├── outputs.tf           # Outputs para outras stacks
├── data.tf              # Data sources (remote state Foundation)
├── backend.tf           # Configuracao do backend S3
├── providers.tf         # Configuracao de providers
├── terraform.tfvars     # Valores das variaveis
└── README.md            # Esta documentacao
```

| Arquivo | Descricao |
|---------|-----------|
| `main.tf` | Instancia modulos MLflow e SageMaker Studio |
| `variables.tf` | Define variaveis de MLflow e Studio |
| `outputs.tf` | Exporta URIs, ARNs e IDs para outras stacks |
| `data.tf` | Le outputs da Foundation via remote state |
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
| `mlflow_environment` | string | `dev` | Ambiente MLflow (dev, stg, prd) |
| `aws_region` | string | `us-east-1` | Regiao AWS |
| `aws_account_id` | string | `888577064416` | ID da conta AWS |

### MLflow

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `tracking_server_size` | string | `Small` | Tamanho do servidor (Small, Medium, Large) |
| `mlflow_version` | string | `3.0` | Versao do MLflow |
| `automatic_model_registration` | bool | `true` | Registro automatico de modelos |
| `weekly_maintenance_window_start` | string | `Sun:03:00` | Janela de manutencao |
| `create_artifact_bucket` | bool | `true` | Criar bucket de artifacts |
| `lifecycle_rules_enabled` | bool | `true` | Habilitar lifecycle rules |
| `artifact_retention_days` | number | `90` | Dias de retencao de artifacts |
| `log_retention_days` | number | `7` | Dias de retencao de logs |

### SageMaker Studio

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `enable_vpc_mode` | bool | `false` | Habilitar modo VPC |
| `default_notebook_instance_type` | string | `ml.t3.medium` | Tipo de instancia |
| `idle_timeout_in_minutes` | number | `60` | Timeout de inatividade (minutos) |
| `sagemaker_user_profile_name` | string | `elo-fraud-ml-user` | Nome do perfil |

### Tags

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `common_tags` | map(string) | (ver variables.tf) | Tags aplicadas a todos os recursos |

> **NOTA:** A integracao MLflow e configurada automaticamente pelo modulo SageMaker Studio
> atraves da variavel `mlflow_tracking_server_name` passada no main.tf.

---

## Outputs

### MLflow

| Output | Descricao |
|--------|-----------|
| `mlflow_tracking_uri` | URI para conexao ao MLflow (arn:aws:sagemaker:...) |
| `mlflow_tracking_server_name` | Nome do servidor MLflow |
| `mlflow_tracking_server_arn` | ARN do servidor |
| `mlflow_tracking_server_url` | URL do MLflow UI (browser) |
| `mlflow_artifact_bucket_arn` | ARN do bucket de artifacts |
| `mlflow_artifact_bucket_name` | Nome do bucket |
| `mlflow_execution_role_arn` | ARN da execution role |

### SageMaker Studio

| Output | Descricao |
|--------|-----------|
| `studio_domain_id` | ID do SageMaker Studio Domain |
| `studio_domain_url` | URL de acesso ao Studio |
| `studio_execution_role_arn` | ARN da execution role |

### Resumo

| Output | Descricao |
|--------|-----------|
| `mlops_summary` | Objeto com resumo completo da stack (environment, region, mlflow, sagemaker_studio) |
| `usage_instructions` | Instrucoes para usar o MLflow em dev com exemplos Python e remote_state |

---

## Guia de Uso

### Conectar ao MLflow via Python

```python
import mlflow

# Configurar tracking URI (use o output do Terraform)
mlflow.set_tracking_uri("arn:aws:sagemaker:us-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-dev")

# Verificar conexao
print(mlflow.get_tracking_uri())

# Criar/selecionar experimento
mlflow.set_experiment("fraud-detection-experiment")

# Logar experimento
with mlflow.start_run():
    # Parametros
    mlflow.log_param("model_type", "xgboost")
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("n_estimators", 100)

    # Metricas
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("precision", 0.92)
    mlflow.log_metric("recall", 0.89)
    mlflow.log_metric("f1_score", 0.90)

    # Modelo
    mlflow.sklearn.log_model(model, "model")
```

### Acessar MLflow UI

```bash
# Obter URL do MLflow UI
terraform output mlflow_tracking_server_url

# Abrir no navegador (requer autenticacao AWS)
# URL formato: https://elo-fraud-mlflow-dev.studio.us-east-1.sagemaker.aws
```

### Acessar SageMaker Studio

```bash
# Obter URL do Studio
terraform output studio_domain_url

# Criar presigned URL para acesso
aws sagemaker create-presigned-domain-url \
  --domain-id $(terraform output -raw studio_domain_id) \
  --user-profile-name elo-fraud-ml-user \
  --region us-east-1
```

### Registrar Modelo no Registry

```python
import mlflow

# Registrar modelo
model_uri = "runs:/<run_id>/model"
mlflow.register_model(model_uri, "fraud-detection-model")

# Promover para staging
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="fraud-detection-model",
    version=1,
    stage="Staging"
)
```

---

## Integracao com Outras Stacks

### Dependencias

```
Foundation ──────▶ MLOps
    │
    └── vpc_id
    └── public_subnet_ids
    └── s3_raw_bucket_arn
    └── s3_processed_bucket_arn
    └── s3_models_bucket_arn
```

### Como Consumir os Outputs

```hcl
# Em outras stacks (ex: Platform-Lambdas)
data "terraform_remote_state" "mlops" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/mlops/terraform.tfstate"
    region = "us-east-1"
  }
}

# Exemplos de uso:
locals {
  mlflow_tracking_uri     = data.terraform_remote_state.mlops.outputs.mlflow_tracking_uri
  mlflow_artifact_bucket  = data.terraform_remote_state.mlops.outputs.mlflow_artifact_bucket_arn
}
```

### Ordem de Implantacao

```
1. bootstrap
       │
       ▼
2. foundation
       │
       ▼
3. mlops          ◀── ESTA STACK
       │
       ▼
4. platform
       │
       ▼
5. platform-k8s
       │
       ▼
6. platform-lambdas
```

---

## Custos Estimados

### Resumo Mensal (DEV)

| Recurso | Configuracao | Custo Estimado |
|---------|--------------|----------------|
| **MLflow Tracking Server** | Small | ~$50.00 |
| **S3 Artifact Storage** | ~10 GB | ~$0.23 |
| **CloudWatch Logs** | ~1 GB | ~$0.50 |
| **SageMaker Studio** | Idle (shutdown) | ~$0.00* |
| **Studio Compute** | ml.t3.medium (uso) | ~$0.05/hora |
| | **Total Base** | **~$51.00** |

> *SageMaker Studio cobra apenas pelo tempo de uso das instancias. Com idle shutdown habilitado, custos sao minimizados.

### Otimizacoes Aplicadas

| Otimizacao | Economia |
|------------|----------|
| MLflow Small (vs Medium/Large) | Significativa |
| Idle Shutdown 60 min | Evita custos ociosos |
| Artifact retention 90 dias | Limita storage |
| Log retention 7 dias | Minimiza logs |

---

## Operacoes

### Verificar Status do MLflow

```bash
# Status do servidor
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev \
  --query 'TrackingServerStatus' \
  --output text

# Deve retornar: Created ou Running
```

### Verificar Studio Domain

```bash
# Status do domain
aws sagemaker describe-domain \
  --domain-id $(terraform output -raw studio_domain_id) \
  --query 'Status' \
  --output text

# Deve retornar: InService
```

### Listar Experimentos MLflow

```python
import mlflow

mlflow.set_tracking_uri("arn:aws:sagemaker:us-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-dev")

# Listar todos os experimentos
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f"{exp.name}: {exp.experiment_id}")
```

### Limpar Artifacts Antigos

```bash
# Listar objetos no bucket de artifacts
aws s3 ls s3://elo-fraud-mlflow-artifacts-dev-888577064416/ --recursive

# Remover artifacts de um experimento especifico
aws s3 rm s3://elo-fraud-mlflow-artifacts-dev-888577064416/experiment-id/ --recursive
```

### Destruir Infraestrutura

```bash
# ATENCAO: Backups de experimentos importantes antes de destruir
# Destruir apenas se nenhuma stack depende desta

terraform destroy
```

---

## Troubleshooting

### Erro: MLflow Tracking Server nao inicia

**Sintoma:**
```
TrackingServerStatus: CreateFailed
```

**Causa:** Problema de permissoes IAM ou configuracao.

**Solucao:**
```bash
# Verificar logs do servidor
aws logs describe-log-streams \
  --log-group-name /aws/sagemaker/mlflow/elo-fraud-mlflow-dev

# Verificar IAM Role
aws iam get-role --role-name elo-fraud-mlflow-execution-role-dev
```

### Erro: Conexao MLflow recusada

**Sintoma:**
```python
mlflow.exceptions.MlflowException: Connection refused
```

**Causa:** Servidor nao esta em estado Running ou URI incorreta.

**Solucao:**
```bash
# Verificar status
aws sagemaker describe-mlflow-tracking-server \
  --tracking-server-name elo-fraud-mlflow-dev

# Usar ARN correto (nao URL)
# Correto: arn:aws:sagemaker:us-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-dev
```

### Erro: SageMaker Studio nao abre

**Sintoma:**
```
Domain status: Failed
```

**Causa:** Problema de VPC, subnet ou permissoes.

**Solucao:**
```bash
# Verificar detalhes do erro
aws sagemaker describe-domain \
  --domain-id $(terraform output -raw studio_domain_id)

# Verificar se subnets existem
aws ec2 describe-subnets --subnet-ids subnet-xxx
```

### Erro: Acesso negado ao S3 do Studio

**Sintoma:**
```
AccessDenied: Access Denied to S3 bucket
```

**Causa:** IAM Role do Studio sem permissoes adequadas.

**Solucao:**
```bash
# Verificar policies da role
aws iam list-attached-role-policies \
  --role-name $(terraform output -raw studio_execution_role_arn | cut -d'/' -f2)

# Verificar bucket policy
aws s3api get-bucket-policy --bucket elo-fraud-raw-dev-888577064416
```

### Erro: Model Registry nao registra automaticamente

**Sintoma:**
Modelos nao aparecem no registry apos treinamento.

**Causa:** `automatic_model_registration` desabilitado ou modelo nao logado corretamente.

**Solucao:**
```python
# Verificar configuracao
import mlflow
print(mlflow.get_registry_uri())

# Registrar manualmente
mlflow.register_model("runs:/<run_id>/model", "model-name")
```
