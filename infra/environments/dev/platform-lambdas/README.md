# Platform-Lambdas Stack - DEV

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

A **Platform-Lambdas Stack** gerencia as funcoes Lambda container-based que dependem de imagens Docker no ECR. Esta separacao resolve o problema de dependencia circular: o ECR e criado vazio pela stack Platform, a imagem e construida pelo CI/CD, e entao esta stack cria a Lambda com a imagem.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Register Best Model** | Lambda que consulta MLflow, identifica o melhor modelo baseado em f1_score e registra no Model Registry |
| **S3 Trigger** | Acionada automaticamente quando objetos sao criados no bucket SageMaker |
| **Model Governance** | Automatiza o processo de promocao de modelos para producao |

### Por que uma Stack Separada?

| Beneficio | Descricao |
|-----------|-----------|
| **Dependencia Circular** | ECR vazio → CI/CD push → Lambda com imagem |
| **Deploy Independente** | Atualizar Lambda sem recriar infraestrutura base |
| **CI/CD Pipeline** | Stack aplicada apos build da imagem Docker |
| **Rollback Isolado** | Reverter Lambda sem afetar outras stacks |

### Fluxo de Deploy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Fluxo de Deploy                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. Platform Stack              2. CI/CD Pipeline                      │
│   ┌─────────────────┐           ┌─────────────────┐                    │
│   │ Cria ECR        │           │ docker build    │                    │
│   │ repository      │──────────▶│ docker push     │                    │
│   │ (vazio)         │           │ to ECR          │                    │
│   └─────────────────┘           └────────┬────────┘                    │
│                                          │                              │
│                                          ▼                              │
│                                 3. Platform-Lambdas Stack               │
│                                 ┌─────────────────┐                    │
│                                 │ Cria Lambda     │                    │
│                                 │ function com    │                    │
│                                 │ imagem ECR      │                    │
│                                 └─────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Arquitetura

```
                              AWS Region: us-east-1
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                         Fluxo: Register Best Model Lambda                       │
│                                                                                 │
│   SageMaker Pipeline                                                            │
│   (Treina modelo)                                                               │
│        │                                                                        │
│        │ Salva artifacts                                                        │
│        ▼                                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  S3 Bucket: sagemaker-us-east-1-888577064416                            │  │
│   │                                                                          │  │
│   │   /elo-fraud/                                                           │  │
│   │   └── training-jobs/                                                    │  │
│   │       └── model-artifacts/                                              │  │
│   │           └── model.tar.gz   ◀──── ObjectCreated Event                  │  │
│   └─────────────────────────────────┬───────────────────────────────────────┘  │
│                                     │                                           │
│                                     │ S3 Notification                           │
│                                     ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  Lambda: elo-fraud-register-best-model-dev                              │  │
│   │                                                                          │  │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│   │  │  Container Image (ECR)                                            │  │  │
│   │  │                                                                    │  │  │
│   │  │  1. Recebe evento S3 (ObjectCreated)                              │  │  │
│   │  │  2. Conecta ao MLflow App via sagemaker-mlflow SDK                │  │  │
│   │  │  3. Lista experimentos do modelo "Felicidade"                     │  │  │
│   │  │  4. Identifica run com melhor metrics.f1_oot                      │  │  │
│   │  │  5. Registra modelo no MLflow Model Registry                      │  │  │
│   │  │  6. Aplica tag "stage=prod" no modelo                             │  │  │
│   │  └───────────────────────────────────────────────────────────────────┘  │  │
│   │                                                                          │  │
│   │  Timeout: 300s | Memory: 512MB                                          │  │
│   └─────────────────────────────────┬───────────────────────────────────────┘  │
│                                     │                                           │
│                                     │ API Calls                                 │
│                                     ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  MLflow App (SageMaker Managed - Serverless)                            │  │
│   │                                                                          │  │
│   │  ARN: arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-XXX       │  │
│   │                                                                          │  │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│   │  │  Model Registry                                                   │  │  │
│   │  │                                                                    │  │  │
│   │  │  Modelo: Felicidade                                               │  │  │
│   │  │  ├── Version 1 (stage=archived)                                   │  │  │
│   │  │  ├── Version 2 (stage=archived)                                   │  │  │
│   │  │  └── Version 3 (stage=prod)  ◀──── Novo melhor modelo             │  │  │
│   │  └───────────────────────────────────────────────────────────────────┘  │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Processamento Detalhado

```
TRIGGER: S3 ObjectCreated
────────────────────────────────────────────────────────────────────────
   SageMaker Pipeline completa treinamento
        │
        ▼
   Salva model.tar.gz em s3://sagemaker-{region}-{account}/
        │
        ▼
   S3 Bucket Notification dispara Lambda
        │
        ▼
   Lambda recebe evento com:
   - bucket_name
   - object_key
   - event_time


PROCESSAMENTO: MLflow Model Registry
────────────────────────────────────────────────────────────────────────
   Lambda inicia processamento
        │
        ▼
   Conecta ao MLflow App via ARN
   (usando sagemaker-mlflow SDK)
        │
        ▼
   Busca experimentos do modelo "Felicidade"
        │
        ▼
   Lista todas as runs com metrica "f1_oot"
        │
        ▼
   Identifica run com melhor f1_oot (maior valor)
        │
        ├──▶ Se nao encontrar ──▶ Retorna erro
        │
        └──▶ Se encontrar ──▶ Registra nova versao no Model Registry
                                      │
                                      ▼
                               Aplica tag "stage=prod"
                                      │
                                      ▼
                               Retorna status de sucesso


RESULTADO: Model Registry Atualizado
────────────────────────────────────────────────────────────────────────
   Modelo disponivel para inference service
        │
        ▼
   Inference Pod (EKS) pode carregar nova versao
   (via envVar MODEL_NAME=Felicidade)
```

---

## Recursos Provisionados

### Lambda Function

#### register-best-model

| Atributo | Valor |
|----------|-------|
| **Nome** | elo-fraud-register-best-model-dev |
| **Descricao** | Registra o melhor modelo do MLflow baseado em training_f1_score |
| **Package Type** | Image (Container) |
| **Image URI** | {account}.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest |
| **Timeout** | 300 segundos (5 minutos) |
| **Memory** | 512 MB |
| **Runtime** | Python 3.12 (via imagem base Lambda) |

##### Environment Variables

| Variavel | Valor | Descricao |
|----------|-------|-----------|
| `ENVIRONMENT` | dev | Ambiente atual |
| `MLFLOW_TRACKING_URI` | arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ | ARN do MLflow App |
| `MODEL_NAME` | Felicidade | Nome do modelo no MLflow |
| `METRIC_TO_COMPARE` | metrics.f1_oot | Metrica para comparar modelos |
| `MLFLOW_BEST_MODEL_RUN` | best_estimator | Tag da run com melhor modelo |
| `MLFLOW_TARGET_TAG_KEY` | stage | Chave da tag de promocao |
| `MLFLOW_TARGET_TAG` | prod | Valor da tag de promocao |

##### IAM Policies

| Policy | Descricao |
|--------|-----------|
| **AWSLambdaBasicExecutionRole** | Permissoes para CloudWatch Logs |
| **AmazonSageMakerFullAccess** | Acesso ao MLflow App e Model Registry |
| **AmazonS3FullAccess** | Acesso ao bucket SageMaker |

> **Nota:** Usa AWS Managed Policies pois SCP bloqueia criacao de custom policies.

### S3 Trigger

| Atributo | Valor |
|----------|-------|
| **Bucket** | sagemaker-us-east-1-888577064416 |
| **Events** | s3:ObjectCreated:* |
| **Filter Prefix** | (nenhum - todos os objetos) |
| **Filter Suffix** | (nenhum - todos os objetos) |

### CloudWatch Log Group

| Atributo | Valor |
|----------|-------|
| **Nome** | /aws/lambda/elo-fraud-register-best-model-dev |
| **Retencao** | 14 dias |

---

## Pre-requisitos

### Dependencias

| Requisito | Descricao |
|-----------|-----------|
| **Platform Stack** | Stack platform aplicada (ECR repository criado) |
| **Imagem Docker** | Imagem construida e pushada para ECR |
| **MLflow App** | MLflow App criado pelo SageMaker Studio Domain |
| **Terraform** | >= 1.10.0 |
| **AWS Provider** | ~> 5.0 |

### Imagem Docker no ECR

A imagem Docker deve existir no ECR antes de aplicar esta stack:

```bash
# Verificar se imagem existe
aws ecr describe-images \
  --repository-name elo-fraud-best-model-register-dev \
  --region us-east-1

# Se nao existir, fazer build e push
cd lambdas/register-best-model
docker build -t elo-fraud-best-model-register-dev .

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

docker tag elo-fraud-best-model-register-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest
```

### Versoes dos Providers

```hcl
terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

---

## Guia de Implantacao

### Primeira Execucao

```bash
# 1. Certifique-se que Platform foi aplicada
cd infra/environments/dev/platform
terraform output ecr_register_best_model_url  # Deve retornar URL do ECR

# 2. Build e push da imagem Docker (se ainda nao feito)
cd ../../../../lambdas/register-best-model

# Login no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t elo-fraud-best-model-register-dev .

# Tag
docker tag elo-fraud-best-model-register-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

# Push
docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

# 3. Navegue ate o diretorio Platform-Lambdas
cd ../../infra/environments/dev/platform-lambdas

# 4. Inicialize o Terraform
terraform init

# 5. Visualize as mudancas
terraform plan

# 6. Aplique os recursos
terraform apply

# 7. Verifique os outputs
terraform output
```

### Verificacao Pos-Implantacao

```bash
# Verificar Lambda criada
aws lambda get-function \
  --function-name elo-fraud-register-best-model-dev \
  --region us-east-1

# Verificar configuracao
aws lambda get-function-configuration \
  --function-name elo-fraud-register-best-model-dev \
  --region us-east-1

# Verificar S3 trigger
aws s3api get-bucket-notification-configuration \
  --bucket sagemaker-us-east-1-888577064416

# Verificar logs
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/elo-fraud-register-best-model-dev \
  --region us-east-1

# Testar Lambda manualmente
aws lambda invoke \
  --function-name elo-fraud-register-best-model-dev \
  --payload '{}' \
  --region us-east-1 \
  /tmp/lambda-response.json

cat /tmp/lambda-response.json
```

---

## Estrutura de Arquivos

### Terraform

```
infra/environments/dev/platform-lambdas/
├── backend.tf       # Backend S3 para state
├── providers.tf     # Provider AWS com default tags
├── data.tf          # Remote state (Platform)
├── variables.tf     # Definicao de variaveis
├── main.tf          # Module lambda (register-best-model)
├── outputs.tf       # Outputs da Lambda
└── README.md        # Esta documentacao
```

### Codigo Fonte da Lambda

```
lambdas/register-best-model/
├── Dockerfile           # Imagem base Lambda Python 3.12
├── requirements.txt     # Dependencias (sagemaker-mlflow, boto3)
├── lambda_handler.py    # Entry point da Lambda
├── best_model_register.py  # Logica de registro no MLflow
├── envs.py              # Carregamento de environment variables
├── utils.py             # Funcoes utilitarias
├── .dockerignore        # Arquivos ignorados no build
└── README.md            # Documentacao do codigo
```

### Descricao dos Arquivos Terraform

| Arquivo | Descricao |
|---------|-----------|
| `backend.tf` | Configuracao do backend S3 com native locking |
| `providers.tf` | Provider AWS com default tags para todos os recursos |
| `data.tf` | Le ECR URL da Platform via terraform_remote_state |
| `variables.tf` | Variaveis do projeto e configuracao do MLflow |
| `main.tf` | Instancia o modulo lambda com configuracoes especificas |
| `outputs.tf` | Exporta ARN, nome e role da Lambda |

---

## Variaveis

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `project_name` | string | `elo-fraud` | Nome do projeto |
| `environment` | string | `dev` | Ambiente |
| `aws_region` | string | `us-east-1` | Regiao AWS |
| `aws_account_id` | string | `888577064416` | ID da conta AWS |
| `mlflow_tracking_uri` | string | `arn:aws:sagemaker:...` | ARN do MLflow App |
| `common_tags` | map(string) | Ver abaixo | Tags comuns |

### Tags Padrao

```hcl
common_tags = {
  Project     = "elo-fraud"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Stack       = "Platform-Lambdas"
  Region      = "us-east-1"
}
```

### Nota sobre mlflow_tracking_uri

O `mlflow_tracking_uri` esta hardcoded intencionalmente:

| Aspecto | Descricao |
|---------|-----------|
| **O que e** | ARN do MLflow App (serverless) criado automaticamente pelo SageMaker Studio |
| **Diferenca** | MLflow App (`mlflow-app/`) e diferente do MLflow Tracking Server (`mlflow-tracking-server/`) |
| **Gerenciamento** | NAO possui recurso Terraform - criado automaticamente |
| **Estabilidade** | ARN e estavel apos criacao do Studio Domain |
| **Atualizacao** | Se Studio Domain for recriado, ARN precisara ser atualizado |

---

## Outputs

| Output | Descricao |
|--------|-----------|
| `lambda_register_best_model_arn` | ARN da Lambda function |
| `lambda_register_best_model_name` | Nome da Lambda function |
| `lambda_register_best_model_role_arn` | ARN da IAM Role da Lambda |

---

## Integracao com Outras Stacks

### Dependencias (Consome)

```
Platform ────────────────▶ Platform-Lambdas
    │
    └── ecr_register_best_model_url
```

### Como Consumir os Outputs

```hcl
# Em data.tf
data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = "elo-fraud-terraform-state-888577064416-us-east-1"
    key    = "dev/platform/terraform.tfstate"
    region = "us-east-1"
  }
}

# Uso via locals
locals {
  ecr_register_best_model_url = data.terraform_remote_state.platform.outputs.ecr_register_best_model_url
}
```

### Ordem de Implantacao

```
1. bootstrap
       │
       ▼
2. foundation
       │
       ├──────────────────┐
       ▼                  ▼
3. mlops            platform
                          │
                          ▼
                    platform-k8s
                          │
                          ▼
                    platform-lambdas  ◀── ESTA STACK (ultima)
```

> **Importante:** Esta e a ultima stack na ordem de implantacao. Requer que a imagem Docker ja tenha sido pushada para o ECR.

---

## Custos Estimados

### Resumo Mensal (DEV)

| Recurso | Quantidade | Custo Unitario | Custo Total |
|---------|------------|----------------|-------------|
| **Lambda Invocations** | ~100/mes | $0.0000002/req | ~$0.00 |
| **Lambda Duration** | ~100 x 30s | $0.0000166667/GB-s | ~$0.25 |
| **CloudWatch Logs** | ~1 GB/mes | $0.50/GB | ~$0.50 |
| **ECR Storage** | ~500 MB | $0.10/GB | ~$0.05 |
| | | **Total Estimado** | **~$0.80** |

### Detalhamento

| Componente | Calculo |
|------------|---------|
| **Lambda** | 512 MB x 30s x 100 invocacoes = 1536 GB-segundos |
| **Free Tier** | 400.000 GB-segundos/mes (cobre uso em dev) |
| **Logs** | Estimativa conservadora para debugging |

> **Nota:** Em dev com baixo volume, custo real sera proximo de $0 devido ao Free Tier.

---

## Operacoes

### Atualizar Imagem Docker

```bash
# 1. Fazer build da nova versao
cd lambdas/register-best-model
docker build -t elo-fraud-best-model-register-dev .

# 2. Login no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

# 3. Tag e push
docker tag elo-fraud-best-model-register-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

# 4. Atualizar Lambda para usar nova imagem
aws lambda update-function-code \
  --function-name elo-fraud-register-best-model-dev \
  --image-uri 888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest \
  --region us-east-1
```

### Invocar Lambda Manualmente

```bash
# Invocacao simples
aws lambda invoke \
  --function-name elo-fraud-register-best-model-dev \
  --payload '{}' \
  --region us-east-1 \
  /tmp/response.json

cat /tmp/response.json

# Invocacao com logs
aws lambda invoke \
  --function-name elo-fraud-register-best-model-dev \
  --payload '{}' \
  --log-type Tail \
  --region us-east-1 \
  /tmp/response.json \
  --query 'LogResult' --output text | base64 -d
```

### Visualizar Logs

```bash
# Ultimos logs
aws logs tail /aws/lambda/elo-fraud-register-best-model-dev \
  --region us-east-1 \
  --follow

# Logs de um periodo especifico
aws logs filter-log-events \
  --log-group-name /aws/lambda/elo-fraud-register-best-model-dev \
  --start-time $(date -d '1 hour ago' +%s000) \
  --region us-east-1

# Buscar erros
aws logs filter-log-events \
  --log-group-name /aws/lambda/elo-fraud-register-best-model-dev \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### Testar Localmente com Docker

```bash
# Na pasta do codigo fonte
cd lambdas/register-best-model

# Build
docker build -t best-model-register-test .

# Executar container
docker run -p 9000:8080 \
  -e MODEL_NAME=Felicidade \
  -e METRIC_TO_COMPARE=metrics.f1_oot \
  -e MLFLOW_TRACKING_URI=arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ \
  -e MLFLOW_BEST_MODEL_RUN=best_estimator \
  -e MLFLOW_TARGET_TAG_KEY=stage \
  -e MLFLOW_TARGET_TAG=prod \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  best-model-register-test

# Em outro terminal, invocar
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{}'
```

### Verificar S3 Trigger

```bash
# Ver configuracao de notificacoes do bucket
aws s3api get-bucket-notification-configuration \
  --bucket sagemaker-us-east-1-888577064416

# Simular trigger (upload de arquivo)
echo "test" > /tmp/test.txt
aws s3 cp /tmp/test.txt s3://sagemaker-us-east-1-888577064416/test/test.txt

# Verificar se Lambda foi invocada (nos logs)
aws logs tail /aws/lambda/elo-fraud-register-best-model-dev \
  --region us-east-1 \
  --since 5m
```

### Destruir Recursos

```bash
# Destruir Lambda e recursos associados
cd infra/environments/dev/platform-lambdas
terraform destroy

# Nota: ECR repository permanece (gerenciado pela Platform stack)
```

---

## Troubleshooting

### Erro: Imagem nao encontrada no ECR

**Sintoma:**
```
Error: InvalidParameterValueException: Source image ... does not exist
```

**Causa:** Imagem Docker nao foi pushada para o ECR.

**Solucao:**
```bash
# Verificar se imagem existe
aws ecr describe-images \
  --repository-name elo-fraud-best-model-register-dev \
  --region us-east-1

# Se nao existir, fazer build e push
cd lambdas/register-best-model
docker build -t elo-fraud-best-model-register-dev .

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  888577064416.dkr.ecr.us-east-1.amazonaws.com

docker tag elo-fraud-best-model-register-dev:latest \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest
```

### Erro: Lambda timeout

**Sintoma:**
```
Task timed out after 300.00 seconds
```

**Causa:** Processamento demorou mais que 5 minutos.

**Solucao:**
```bash
# Verificar logs para identificar onde travou
aws logs tail /aws/lambda/elo-fraud-register-best-model-dev \
  --region us-east-1 \
  --since 10m

# Possiveis causas:
# - Muitos experimentos no MLflow
# - Conexao lenta com MLflow App
# - Bug no codigo

# Se necessario, aumentar timeout no main.tf:
# timeout = 600  # 10 minutos
```

### Erro: Access Denied ao MLflow

**Sintoma:**
```
AccessDeniedException: User is not authorized to perform sagemaker:DescribeMlflowTrackingServer
```

**Causa:** IAM Role da Lambda sem permissoes.

**Solucao:**
```bash
# Verificar policies anexadas
aws iam list-attached-role-policies \
  --role-name $(terraform output -raw lambda_register_best_model_role_arn | cut -d'/' -f2) \
  --region us-east-1

# Deve ter AmazonSageMakerFullAccess
# Se nao tiver, verificar main.tf managed_policy_arns
```

### Erro: S3 Trigger nao dispara Lambda

**Sintoma:**
Lambda nao e invocada quando arquivo e criado no S3.

**Causa:** Notificacao S3 nao configurada corretamente.

**Solucao:**
```bash
# Verificar configuracao de notificacoes
aws s3api get-bucket-notification-configuration \
  --bucket sagemaker-us-east-1-888577064416

# Deve mostrar LambdaFunctionConfigurations com ARN da Lambda

# Verificar permissao da Lambda para ser invocada pelo S3
aws lambda get-policy \
  --function-name elo-fraud-register-best-model-dev \
  --region us-east-1

# Se bucket notification sobrescreveu a configuracao:
# Re-aplicar terraform para recriar
terraform apply
```

### Erro: Modelo nao encontrado no MLflow

**Sintoma:**
```
ModelNotFoundException: Model 'Felicidade' not found
```

**Causa:** Modelo ainda nao foi registrado no MLflow ou nome incorreto.

**Solucao:**
```bash
# Verificar environment variables
aws lambda get-function-configuration \
  --function-name elo-fraud-register-best-model-dev \
  --region us-east-1 \
  --query 'Environment.Variables'

# MODEL_NAME deve ser "Felicidade"

# Verificar se modelo existe no MLflow (via UI ou SDK)
# Pode ser necessario criar primeiro experimento/run
```

### Erro: ECR repository nao encontrado no remote state

**Sintoma:**
```
Error: Unsupported attribute "ecr_register_best_model_url"
```

**Causa:** Stack Platform nao foi aplicada ou output nao existe.

**Solucao:**
```bash
# Verificar se Platform tem o output
cd ../platform
terraform output ecr_register_best_model_url

# Se nao existir, verificar se storage.tf tem o ECR resource
# e outputs.tf exporta o valor

# Re-aplicar Platform se necessario
terraform apply
```

### Erro: Container Image manifest not found

**Sintoma:**
```
Error: Image manifest for ... was not found
```

**Causa:** Tag :latest nao existe no ECR.

**Solucao:**
```bash
# Listar tags disponiveis
aws ecr list-images \
  --repository-name elo-fraud-best-model-register-dev \
  --region us-east-1

# Se nao houver :latest, fazer push com essa tag
docker tag <image-id> \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest

docker push \
  888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-best-model-register-dev:latest
```

