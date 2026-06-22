# Modulo Lambda

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Modos de Deploy](#modos-de-deploy)
- [S3 Trigger](#s3-trigger)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona uma **AWS Lambda Function** com suporte a dois modos de deploy: codigo fonte empacotado (Zip) ou imagem de container (ECR).

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Serverless Computing** | Execucao de codigo sem gerenciamento de servidores |
| **Event-Driven** | Integracao com eventos S3, SQS, API Gateway, etc. |
| **Dual Deploy Mode** | Suporte a Zip (codigo fonte) e Container Image (ECR) |
| **Auto-Scaling** | Escala automaticamente com a demanda |

### Caracteristicas Principais

| Caracteristica | Valor Padrao | Descricao |
|----------------|--------------|-----------|
| **Runtime** | python3.12 | Runtime padrao (modo Zip) |
| **Timeout** | 60 segundos | Tempo maximo de execucao |
| **Memory** | 256 MB | Memoria alocada |
| **Log Retention** | 14 dias | Retencao de logs no CloudWatch |
| **Package Type** | Zip ou Image | Configuravel via variavel |

---

## Arquitetura

```
                              AWS Lambda Function
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   MODO ZIP                                 MODO CONTAINER                       │
│                                                                                 │
│   ┌─────────────────┐                     ┌─────────────────┐                  │
│   │  Source Code    │                     │      ECR        │                  │
│   │  (source_path)  │                     │   (image_uri)   │                  │
│   └────────┬────────┘                     └────────┬────────┘                  │
│            │                                       │                            │
│            │  archive_file                         │  Pull Image                │
│            ▼                                       ▼                            │
│   ┌─────────────────┐                     ┌─────────────────┐                  │
│   │    .zip file    │                     │  Container      │                  │
│   │                 │                     │  Runtime        │                  │
│   └────────┬────────┘                     └────────┬────────┘                  │
│            │                                       │                            │
│            └───────────────────┬───────────────────┘                           │
│                                │                                                │
│                                ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                        Lambda Function                                   │  │
│   │                                                                          │  │
│   │   Nome: {function_name}                                                 │  │
│   │                                                                          │  │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│   │   │  IAM Role   │  │  Env Vars   │  │  Log Group  │                    │  │
│   │   │             │  │             │  │             │                    │  │
│   │   │ - Basic     │  │ ENVIRONMENT │  │ /aws/lambda │  │
│   │   │   Execution │  │ + custom    │  │ /{func}     │                    │  │
│   │   └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                │                                                │
│                                │  Invocation                                    │
│                                ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                           Triggers                                       │  │
│   │                                                                          │  │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│   │   │   S3    │  │   SQS   │  │   API   │  │ EventBr │  │Schedule │     │  │
│   │   │ Bucket  │  │  Queue  │  │ Gateway │  │  idge   │  │  (cron) │     │  │
│   │   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fluxo com S3 Trigger

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              S3 Trigger Flow                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐             │
│   │  S3 Bucket    │      │  S3 Event     │      │    Lambda     │             │
│   │               │─────▶│  Notification │─────▶│   Function    │             │
│   │  PUT object   │      │               │      │               │             │
│   └───────────────┘      └───────────────┘      └───────────────┘             │
│                                                         │                      │
│   Filtros opcionais:                                    │                      │
│   - prefix: "incoming/"                                 ▼                      │
│   - suffix: ".json"                          ┌───────────────┐                │
│                                              │   Processar   │                │
│                                              │   Arquivo     │                │
│                                              └───────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

### AWS Resources

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| **IAM Role** | `aws_iam_role` | Role para execucao da Lambda |
| **IAM Policy Attachment** | `aws_iam_role_policy_attachment` | Basic Execution + Managed Policies |
| **CloudWatch Log Group** | `aws_cloudwatch_log_group` | Logs da funcao |
| **Lambda Function (Zip)** | `aws_lambda_function` | Funcao com codigo empacotado |
| **Lambda Function (Container)** | `aws_lambda_function` | Funcao com imagem ECR |
| **Lambda Permission** | `aws_lambda_permission` | Permissao para S3 invocar (opcional) |
| **S3 Notification** | `aws_s3_bucket_notification` | Trigger S3 (opcional) |

### Diagrama de Recursos

```
aws_iam_role.lambda
    │
    ├── aws_iam_role_policy_attachment.lambda_basic
    │       └── AWSLambdaBasicExecutionRole
    │
    └── aws_iam_role_policy_attachment.managed_policies[]
            └── Custom managed policies

aws_cloudwatch_log_group.lambda
    └── /aws/lambda/{function_name}

aws_lambda_function.zip (ou .container)
    │
    ├── Depends on: log_group, iam_role
    │
    └── (opcional) aws_lambda_permission.s3_trigger
            │
            └── aws_s3_bucket_notification.lambda_trigger
```

---

## Modos de Deploy

O modulo suporta dois modos de deploy, controlados pela variavel `use_container_image`.

### Modo Zip (Padrao)

Deploy com codigo fonte empacotado automaticamente em arquivo .zip.

| Atributo | Descricao |
|----------|-----------|
| **Package Type** | Zip |
| **Variavel de Controle** | `use_container_image = false` |
| **Requer** | `source_path` (diretorio com codigo) |
| **Handler** | Configuravel (ex: `handler.lambda_handler`) |
| **Runtime** | Configuravel (ex: `python3.12`) |

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "dev"
  function_name = "elo-fraud-etl-processor-dev"

  use_container_image = false
  source_path         = "${path.module}/src"
  handler             = "handler.lambda_handler"
  runtime             = "python3.12"
}
```

### Modo Container Image

Deploy com imagem Docker armazenada no ECR.

| Atributo | Descricao |
|----------|-----------|
| **Package Type** | Image |
| **Variavel de Controle** | `use_container_image = true` |
| **Requer** | `image_uri` (URI da imagem ECR) |
| **Handler** | Definido na imagem (ENTRYPOINT/CMD) |
| **Runtime** | Definido na imagem |

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "dev"
  function_name = "elo-fraud-ml-inference-dev"

  use_container_image = true
  image_uri           = "888577064416.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-model-dev:latest"
}
```

### Comparativo

| Aspecto | Modo Zip | Modo Container |
|---------|----------|----------------|
| **Tamanho Maximo** | 250 MB (descompactado) | 10 GB |
| **Dependencias** | Lambda Layers ou empacotadas | Incluidas na imagem |
| **Cold Start** | Mais rapido | Mais lento |
| **Flexibilidade** | Limitado aos runtimes AWS | Qualquer runtime |
| **CI/CD** | Simples | Requer build de imagem |
| **Caso de Uso** | Scripts simples, ETL leve | ML, dependencias complexas |

---

## S3 Trigger

O modulo suporta configuracao de trigger S3 opcional para invocar a Lambda quando objetos sao criados/modificados em um bucket.

### Configuracao

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `enable_s3_trigger` | bool | Habilitar trigger S3 |
| `s3_trigger_bucket_name` | string | Nome do bucket |
| `s3_trigger_events` | list(string) | Eventos que disparam (default: `s3:ObjectCreated:*`) |
| `s3_trigger_filter_prefix` | string | Filtro por prefixo (opcional) |
| `s3_trigger_filter_suffix` | string | Filtro por sufixo (opcional) |

### Eventos Suportados

| Evento | Descricao |
|--------|-----------|
| `s3:ObjectCreated:*` | Qualquer criacao de objeto |
| `s3:ObjectCreated:Put` | PUT de objeto |
| `s3:ObjectCreated:Post` | POST de objeto |
| `s3:ObjectCreated:Copy` | Copia de objeto |
| `s3:ObjectRemoved:*` | Qualquer remocao de objeto |

### Exemplo com Filtros

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "dev"
  function_name = "elo-fraud-file-processor-dev"

  source_path = "${path.module}/src"

  # S3 Trigger
  enable_s3_trigger        = true
  s3_trigger_bucket_name   = "elo-fraud-incoming-dev"
  s3_trigger_events        = ["s3:ObjectCreated:Put"]
  s3_trigger_filter_prefix = "incoming/"
  s3_trigger_filter_suffix = ".json"
}
```

---

## Uso

### Uso Basico (Modo Zip)

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "dev"
  function_name = "elo-fraud-data-processor-dev"

  source_path = "${path.module}/lambda-code"
}
```

### Uso com Container Image

```hcl
module "lambda" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "staging"
  function_name = "elo-fraud-ml-inference-staging"

  use_container_image = true
  image_uri           = module.ecr.model_repository_url

  timeout     = 120
  memory_size = 1024
}
```

### Uso Completo

```hcl
module "lambda" {
  source = "../../modules/lambda"

  # Identificacao
  project_name  = "elo-fraud"
  environment   = "prod"
  function_name = "elo-fraud-etl-processor-prod"
  description   = "Processa arquivos de transacoes do S3"

  # Deploy Mode
  use_container_image = false
  source_path         = "${path.module}/lambda-code"
  handler             = "main.handler"
  runtime             = "python3.12"

  # Performance
  timeout     = 300
  memory_size = 512

  # Variaveis de Ambiente
  environment_variables = {
    DYNAMODB_TABLE = module.dynamodb.table_name
    S3_BUCKET      = module.s3.bucket_name
    LOG_LEVEL      = "INFO"
  }

  # IAM - Managed Policies adicionais
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  ]

  # S3 Trigger
  enable_s3_trigger        = true
  s3_trigger_bucket_name   = module.s3.incoming_bucket_name
  s3_trigger_events        = ["s3:ObjectCreated:*"]
  s3_trigger_filter_prefix = "transactions/"
  s3_trigger_filter_suffix = ".json"

  # Logs
  log_retention_days = 30

  # Tags
  tags = {
    Team    = "data-engineering"
    Purpose = "etl"
  }
}
```

### Multiplas Lambdas

```hcl
# Lambda para processar arquivos
module "lambda_processor" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "staging"
  function_name = "elo-fraud-file-processor-staging"

  source_path = "${path.module}/processor"

  enable_s3_trigger      = true
  s3_trigger_bucket_name = module.s3.incoming_bucket_name
}

# Lambda para API
module "lambda_api" {
  source = "../../modules/lambda"

  project_name  = "elo-fraud"
  environment   = "staging"
  function_name = "elo-fraud-api-handler-staging"

  source_path = "${path.module}/api"
  timeout     = 30
  memory_size = 128
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `project_name` | string | Sim | - | Nome do projeto |
| `environment` | string | Sim | - | Ambiente (dev, stg, prd) |
| `function_name` | string | Sim | - | Nome da funcao Lambda |
| `description` | string | Nao | `""` | Descricao da funcao |

### Deploy Mode

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `use_container_image` | bool | Nao | `false` | Se true, usa container image |
| `source_path` | string | Condicional | `null` | Caminho do codigo (modo Zip) |
| `image_uri` | string | Condicional | `null` | URI da imagem ECR (modo Container) |

### Runtime (Modo Zip)

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `handler` | string | Nao | `handler.lambda_handler` | Handler da funcao |
| `runtime` | string | Nao | `python3.12` | Runtime da Lambda |

### Performance

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `timeout` | number | Nao | `60` | Timeout em segundos (max 900) |
| `memory_size` | number | Nao | `256` | Memoria em MB (128-10240) |

### Variaveis de Ambiente

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `environment_variables` | map(string) | Nao | `{}` | Variaveis de ambiente |

### IAM

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `managed_policy_arns` | list(string) | Nao | `[]` | ARNs de AWS Managed Policies |

### S3 Trigger

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `enable_s3_trigger` | bool | Nao | `false` | Habilitar trigger S3 |
| `s3_trigger_bucket_name` | string | Condicional | `""` | Nome do bucket |
| `s3_trigger_events` | list(string) | Nao | `["s3:ObjectCreated:*"]` | Eventos S3 |
| `s3_trigger_filter_prefix` | string | Nao | `null` | Filtro de prefixo |
| `s3_trigger_filter_suffix` | string | Nao | `null` | Filtro de sufixo |

### CloudWatch Logs

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `log_retention_days` | number | Nao | `14` | Dias de retencao dos logs |

### Tags

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tags` | map(string) | Nao | `{}` | Tags adicionais |

---

## Outputs

### Funcao Lambda

| Output | Tipo | Descricao |
|--------|------|-----------|
| `function_name` | string | Nome da funcao Lambda |
| `function_arn` | string | ARN da funcao Lambda |
| `invoke_arn` | string | ARN para invocacao (API Gateway) |

### IAM

| Output | Tipo | Descricao |
|--------|------|-----------|
| `role_arn` | string | ARN da IAM Role |

### CloudWatch

| Output | Tipo | Descricao |
|--------|------|-----------|
| `log_group_name` | string | Nome do CloudWatch Log Group |

### S3 Trigger

| Output | Tipo | Descricao |
|--------|------|-----------|
| `s3_trigger_bucket` | string | Nome do bucket configurado (ou null) |

### Auxiliares

| Output | Tipo | Descricao |
|--------|------|-----------|
| `package_type` | string | Tipo de pacote (Zip ou Image) |
| `lambda_summary` | object | Resumo completo da configuracao (ver estrutura abaixo) |

### Estrutura do lambda_summary

```hcl
{
  function_name      = "elo-fraud-my-lambda-dev"
  function_arn       = "arn:aws:lambda:sa-east-1:123456789:function:..."
  package_type       = "Image"  # ou "Zip"
  image_uri          = "123456789.dkr.ecr.sa-east-1.amazonaws.com/repo:tag"
  timeout            = 60
  memory_size        = 256
  role_arn           = "arn:aws:iam::123456789:role/..."
  log_group          = "/aws/lambda/elo-fraud-my-lambda-dev"
  s3_trigger_enabled = false
  s3_trigger_bucket  = null
}
```

> **Nota**: Os campos `handler` e `runtime` nao estao incluidos no summary pois sao especificos do modo Zip e definidos internamente no container quando `use_container_image = true`.

### Exemplo de Uso dos Outputs

```hcl
# Referenciar ARN em outra resource
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.main.arn
  function_name    = module.lambda.function_arn
}

# Usar invoke_arn no API Gateway
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.main.id
  http_method = aws_api_gateway_method.main.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda.invoke_arn
}

# Output do summary
output "lambda_config" {
  value = module.lambda.lambda_summary
}
```

---

## Operacoes

### Listar Funcoes

```bash
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `elo-fraud`)].FunctionName' \
  --region sa-east-1
```

### Descrever Funcao

```bash
aws lambda get-function \
  --function-name elo-fraud-etl-processor-dev \
  --region sa-east-1
```

### Invocar Funcao (Teste)

```bash
# Invocacao sincrona
aws lambda invoke \
  --function-name elo-fraud-etl-processor-dev \
  --payload '{"test": true}' \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --region sa-east-1

# Ver resposta
cat response.json
```

### Ver Logs

```bash
# Ultimos logs
aws logs tail /aws/lambda/elo-fraud-etl-processor-dev \
  --region sa-east-1 \
  --follow

# Logs das ultimas 2 horas
aws logs filter-log-events \
  --log-group-name /aws/lambda/elo-fraud-etl-processor-dev \
  --start-time $(date -d '2 hours ago' +%s)000 \
  --region sa-east-1
```

### Atualizar Codigo (Zip)

```bash
# Reempacotar e atualizar
zip -r function.zip .
aws lambda update-function-code \
  --function-name elo-fraud-etl-processor-dev \
  --zip-file fileb://function.zip \
  --region sa-east-1
```

### Atualizar Imagem (Container)

```bash
aws lambda update-function-code \
  --function-name elo-fraud-ml-inference-dev \
  --image-uri 888577064416.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-model-dev:v1.2.0 \
  --region sa-east-1
```

### Verificar Configuracao

```bash
# Ver variaveis de ambiente
aws lambda get-function-configuration \
  --function-name elo-fraud-etl-processor-dev \
  --query 'Environment.Variables' \
  --region sa-east-1

# Ver timeout e memoria
aws lambda get-function-configuration \
  --function-name elo-fraud-etl-processor-dev \
  --query '{Timeout: Timeout, Memory: MemorySize}' \
  --region sa-east-1
```

### Ver Metricas

```bash
# Invocacoes na ultima hora
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=elo-fraud-etl-processor-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region sa-east-1

# Erros
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=elo-fraud-etl-processor-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region sa-east-1
```

---

## Troubleshooting

### Erro: Access Denied

**Sintoma**:
```
AccessDeniedException: User is not authorized to perform: dynamodb:PutItem
```

**Causa**: IAM Role sem permissao necessaria.

**Solucao**: Adicionar managed policy ou criar inline policy:
```hcl
module "lambda" {
  # ...
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  ]
}
```

---

### Erro: Task timed out

**Sintoma**:
```
Task timed out after 60.00 seconds
```

**Causa**: Timeout insuficiente para a operacao.

**Solucao**: Aumentar timeout:
```hcl
module "lambda" {
  # ...
  timeout = 300  # 5 minutos
}
```

---

### Erro: Memory Size exceeded

**Sintoma**:
```
Runtime exited with error: signal: killed
```

**Causa**: Memoria insuficiente (OOM).

**Solucao**: Aumentar memoria:
```hcl
module "lambda" {
  # ...
  memory_size = 1024  # 1 GB
}
```

---

### Erro: Handler not found

**Sintoma**:
```
Unable to import module 'handler': No module named 'handler'
```

**Causa**: Handler incorreto ou estrutura de diretorios errada.

**Solucao**: Verificar estrutura e handler:
```bash
# Estrutura esperada para handler = "handler.lambda_handler"
src/
└── handler.py  # deve conter funcao lambda_handler()
```

```hcl
module "lambda" {
  # ...
  handler = "handler.lambda_handler"  # arquivo.funcao
}
```

---

### Erro: S3 Trigger nao funciona

**Sintoma**: Objetos criados no S3 nao invocam a Lambda.

**Verificar**:
```bash
# 1. Verificar permissao da Lambda
aws lambda get-policy \
  --function-name elo-fraud-etl-processor-dev \
  --region sa-east-1

# 2. Verificar notificacao do bucket
aws s3api get-bucket-notification-configuration \
  --bucket elo-fraud-incoming-dev

# 3. Verificar filtros de prefixo/sufixo
# O arquivo deve corresponder aos filtros configurados
```

---

### Erro: Container Image not found

**Sintoma**:
```
Image does not exist or is not accessible
```

**Causa**: URI da imagem incorreto ou permissao ECR.

**Solucao**:
```bash
# Verificar se imagem existe
aws ecr describe-images \
  --repository-name elo-fraud-model-dev \
  --image-ids imageTag=latest \
  --region sa-east-1

# Lambda precisa de permissao no ECR (automatico na mesma conta)
```

---

### Verificar Saude da Lambda

```bash
# Configuracao completa
aws lambda get-function \
  --function-name elo-fraud-etl-processor-dev \
  --region sa-east-1

# Estado da funcao
aws lambda get-function \
  --function-name elo-fraud-etl-processor-dev \
  --query 'Configuration.State' \
  --region sa-east-1

# Ultima atualizacao
aws lambda get-function \
  --function-name elo-fraud-etl-processor-dev \
  --query 'Configuration.LastModified' \
  --region sa-east-1
```

---

## Custos Estimados

### Precos (sa-east-1)

| Componente | Preco |
|------------|-------|
| **Requests** | $0.20 / 1 milhao requests |
| **Duration** | $0.0000166667 / GB-segundo |
| **Free Tier** | 1M requests + 400.000 GB-s / mes |

### Estimativa por Volume

| Cenario | Invocacoes/Mes | Duracao Media | Custo Estimado |
|---------|----------------|---------------|----------------|
| **Dev** | 10.000 | 1s @ 256MB | ~$0.04 |
| **Staging** | 100.000 | 2s @ 512MB | ~$1.50 |
| **Prod** | 1.000.000 | 3s @ 1GB | ~$50.00 |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Dual deploy mode** | Flexibilidade para casos simples (Zip) e complexos (Container) |
| **use_container_image explicito** | Evita problemas de count dinamico no Terraform |
| **Basic Execution Role padrao** | Permissoes minimas, adicionar conforme necessidade |
| **Log Group pre-criado** | Garante configuracao de retencao desde o inicio |
| **S3 Trigger opcional** | Padrao comum, mas desabilitado por padrao |
| **Environment variable ENVIRONMENT** | Sempre disponivel para a aplicacao |

---

## Referencias

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Lambda with S3](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)
- [Lambda Quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
