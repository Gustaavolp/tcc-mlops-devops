# Modulo API Gateway

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Endpoints](#endpoints)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [VPC Link](#vpc-link)
- [Rate Limiting](#rate-limiting)
- [Logs e Metricas](#logs-e-metricas)
- [Exemplos](#exemplos)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo cria uma **REST API no Amazon API Gateway** com integracao privada via VPC Link. O trafego entre API Gateway e o backend nao passa pela internet publica.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Ponto de Entrada** | API REST para autorizacao de compras online |
| **Rate Limiting** | Protecao contra abuso com throttling configuravel |
| **API Keys** | Identificacao de clientes e rate limiting por cliente |
| **VPC Link** | Integracao privada com NLB/ALB internos |

### Caracteristicas Principais

| Caracteristica | Valor Padrao | Descricao |
|----------------|--------------|-----------|
| **Tipo** | REST API | API Gateway REST (nao HTTP API) |
| **Endpoint** | REGIONAL | Latencia otimizada para regiao |
| **Integracao** | HTTP_PROXY | Proxy via VPC Link (trafego interno) |
| **Rate Limit** | 10000 req/s | Configuravel |
| **Burst Limit** | 5000 req | Configuravel |

---

## Arquitetura

### Trafego Interno via VPC Link

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ARQUITETURA: VPC LINK (trafego interno)                                  │
│                                                                             │
│   ┌──────────┐      ┌─────────────────┐      ┌──────────────────────────┐ │
│   │          │      │                 │      │         VPC              │ │
│   │  Cliente │─────▶│  API Gateway    │─────▶│  ┌─────┐    ┌─────┐     │ │
│   │          │      │                 │      │  │ NLB │───▶│ ALB │     │ │
│   └──────────┘      │  VPC_LINK       │      │  │(int)│    │(int)│     │ │
│                     │                 │      │  └─────┘    └──┬──┘     │ │
│                     └────────┬────────┘      │                │        │ │
│                              │               │                ▼        │ │
│                              │  VPC Link     │           ┌────────┐   │ │
│                              └───────────────┼──────────▶│  EKS   │   │ │
│                                              │           └────────┘   │ │
│                                              └──────────────────────────┘ │
│                                                                             │
│   Fluxo: Cliente → API Gateway → VPC Link → NLB → ALB → EKS               │
│                                                                             │
│   Vantagens:                                                               │
│   - ALB/NLB privados (nao expostos a internet)                            │
│   - Trafego interno na rede AWS                                            │
│   - Maior seguranca                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Decisao de Arquitetura

| Aspecto | Configuracao |
|---------|--------------|
| **Tipo de Conexao** | VPC_LINK (sempre) |
| **Backend** | NLB interno → ALB interno → EKS |
| **Seguranca** | ALB/NLB nao expostos a internet |
| **Latencia** | Rede interna AWS |

---

## Recursos Criados

### AWS Resources

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| **REST API** | `aws_api_gateway_rest_api` | API REST principal |
| **Resources** | `aws_api_gateway_resource` | /authorize-purchase, /health |
| **Methods** | `aws_api_gateway_method` | POST /authorize-purchase, GET /health |
| **Integrations** | `aws_api_gateway_integration` | HTTP_PROXY para backend |
| **Deployment** | `aws_api_gateway_deployment` | Deploy da API |
| **Stage** | `aws_api_gateway_stage` | Stage v1 |
| **VPC Link** | `aws_api_gateway_vpc_link` | Conexao privada via NLB |
| **Usage Plan** | `aws_api_gateway_usage_plan` | Rate limiting por API Key (opcional) |
| **API Keys** | `aws_api_gateway_api_key` | Chaves para identificacao de clientes (opcional) |
| **Log Group** | `aws_cloudwatch_log_group` | Logs de acesso |

### Diagrama de Recursos

```
aws_api_gateway_rest_api.main
    │
    ├── aws_api_gateway_resource.authorize_purchase (/authorize-purchase)
    │       │
    │       └── aws_api_gateway_method.post_authorize_purchase (POST)
    │               └── aws_api_gateway_integration.post_authorize_purchase
    │
    ├── aws_api_gateway_resource.health (/health)
    │       │
    │       └── aws_api_gateway_method.get_health (GET)
    │               └── aws_api_gateway_integration.get_health
    │
    ├── aws_api_gateway_deployment.main
    │       │
    │       └── aws_api_gateway_stage.main (v1)
    │               │
    │               └── aws_api_gateway_method_settings.all
    │
    ├── aws_api_gateway_vpc_link.main
    │
    ├── aws_api_gateway_usage_plan.main (opcional)
    │       │
    │       └── aws_api_gateway_usage_plan_key.keys
    │
    └── aws_api_gateway_api_key.keys (opcional)
```

---

## Endpoints

### URLs Geradas

| Endpoint | Metodo | URL | Descricao |
|----------|--------|-----|-----------|
| **Authorize Purchase** | POST | `{invoke_url}/authorize-purchase` | Autorizacao de compra |
| **Health** | GET | `{invoke_url}/health` | Health check |

### Formato da URL

```
https://{api_id}.execute-api.{region}.amazonaws.com/{stage}/{resource}

Exemplo:
https://abc123xyz.execute-api.us-east-1.amazonaws.com/v1/authorize-purchase
```

### Exemplos de Uso

```bash
# Health check (nao requer API Key)
curl -X GET https://API_ID.execute-api.REGION.amazonaws.com/v1/health

# Authorize Purchase (sem API Key - quando enable_usage_plan = false)
curl -X POST https://API_ID.execute-api.REGION.amazonaws.com/v1/authorize-purchase \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "tx-123", "amount": 1500}'

# Authorize Purchase (com API Key - quando enable_usage_plan = true)
curl -X POST https://API_ID.execute-api.REGION.amazonaws.com/v1/authorize-purchase \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"transaction_id": "tx-123", "amount": 1500}'
```

---

## Uso

### Exemplo Basico

```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  project_name = "elo-fraud"
  environment  = "dev"
  api_name     = "elo-fraud-api-dev"

  # VPC Link (obrigatorio)
  nlb_arn      = module.nlb.nlb_arn
  nlb_dns_name = module.nlb.nlb_dns_name
}
```

### Exemplo Completo (com API Keys)

```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  # Identificacao
  project_name    = "elo-fraud"
  environment     = "dev"
  api_name        = "elo-fraud-api-dev"
  api_description = "API de Autorizacao de Compras Online"

  # VPC Link (trafego interno)
  nlb_arn      = module.nlb.nlb_arn
  nlb_dns_name = module.nlb.nlb_dns_name

  # API Configuration
  endpoint_configuration_type = "REGIONAL"
  stage_name                  = "v1"

  # Logs
  enable_access_logs = true
  log_retention_days = 7

  # Throttling (stage level)
  throttle_burst_limit = 5000
  throttle_rate_limit  = 10000

  # Usage Plan (rate limiting por API Key)
  enable_usage_plan               = true
  usage_plan_quota_limit          = 1000000
  usage_plan_quota_period         = "MONTH"
  usage_plan_throttle_burst_limit = 2000
  usage_plan_throttle_rate_limit  = 1000

  # API Keys
  api_keys = {
    "elo-backend" = {
      enabled     = true
      description = "API Key para backend Elo"
    }
    "testing" = {
      enabled     = true
      description = "API Key para testes"
    }
  }

  # Tags
  tags = {
    Team = "platform"
  }
}
```

---

## Variaveis

### Identificacao

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `project_name` | string | Sim | - | Nome do projeto |
| `environment` | string | Sim | - | Ambiente (dev, staging, prod) |
| `api_name` | string | Sim | - | Nome da API Gateway |
| `api_description` | string | Nao | "API de Autorizacao de Compras Online - Real-time purchase authorization" | Descricao da API |

> **Convencao de nomenclatura recomendada para `api_name`:**
> ```
> {project_name}-api-{environment}
> ```
> Exemplos: `elo-fraud-api-dev`, `elo-fraud-api-staging`, `elo-fraud-api-prod`

### VPC Link (trafego interno)

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `nlb_arn` | string | Sim | - | ARN do NLB para VPC Link |
| `nlb_dns_name` | string | Sim | - | DNS name do NLB |

### API Configuration

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `endpoint_configuration_type` | string | Nao | `"REGIONAL"` | REGIONAL, EDGE, PRIVATE |
| `stage_name` | string | Nao | `"v1"` | Nome do stage |
| `enable_access_logs` | bool | Nao | `true` | Habilitar logs |
| `log_retention_days` | number | Nao | `7` | Retencao de logs (dias) |

### Throttling

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `throttle_burst_limit` | number | Nao | `5000` | Burst limit (requests) |
| `throttle_rate_limit` | number | Nao | `10000` | Rate limit (req/s) |

### Usage Plan

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `enable_usage_plan` | bool | Nao | `false` | Habilitar Usage Plan com API Keys |
| `usage_plan_quota_limit` | number | Nao | `1000000` | Quota de requests por periodo |
| `usage_plan_quota_period` | string | Nao | `"MONTH"` | DAY, WEEK, MONTH |
| `usage_plan_throttle_burst_limit` | number | Nao | `2000` | Burst limit por API Key |
| `usage_plan_throttle_rate_limit` | number | Nao | `1000` | Rate limit por API Key (req/s) |

### API Keys

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `api_keys` | map(object) | Nao | `{}` | Mapa de API Keys {name = {enabled, description}} |

### Tags

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tags` | map(string) | Nao | `{}` | Tags adicionais |

---

## Outputs

### REST API

| Output | Tipo | Descricao |
|--------|------|-----------|
| `rest_api_id` | string | ID da REST API |
| `rest_api_arn` | string | ARN da REST API |
| `rest_api_execution_arn` | string | Execution ARN (para permissoes) |
| `rest_api_root_resource_id` | string | ID do resource raiz |

### Stage

| Output | Tipo | Descricao |
|--------|------|-----------|
| `stage_name` | string | Nome do stage |
| `stage_arn` | string | ARN do stage |
| `stage_invoke_url` | string | URL de invocacao |

### Endpoints

| Output | Tipo | Descricao |
|--------|------|-----------|
| `api_endpoint` | string | URL base (sem stage) |
| `authorize_purchase_endpoint_url` | string | URL do POST /authorize-purchase |
| `health_endpoint_url` | string | URL do GET /health |

### VPC Link

| Output | Tipo | Descricao |
|--------|------|-----------|
| `vpc_link_id` | string | ID do VPC Link |
| `vpc_link_arn` | string | ARN do VPC Link |
| `vpc_link_name` | string | Nome do VPC Link |

### Usage Plan e API Keys

| Output | Tipo | Descricao |
|--------|------|-----------|
| `usage_plan_id` | string | ID do Usage Plan |
| `usage_plan_arn` | string | ARN do Usage Plan |
| `api_key_ids` | map(string) | Mapa de API Key names → IDs |
| `api_key_values` | map(string) | Mapa de API Key names → valores (sensitive) |

### Logs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `cloudwatch_log_group_name` | string | Nome do log group |
| `cloudwatch_log_group_arn` | string | ARN do log group |

### Auxiliares

| Output | Tipo | Descricao |
|--------|------|-----------|
| `api_gateway_summary` | object | Resumo da configuracao |
| `curl_examples` | string | Exemplos de uso com curl |

---

## VPC Link

### O que e VPC Link?

VPC Link permite que o API Gateway acesse recursos em VPCs privadas sem expor esses recursos na internet.

### Requisitos

1. **NLB Interno**: Network Load Balancer como target do VPC Link
2. **ALB Interno**: Application Load Balancer recebendo trafego do NLB
3. **Security Groups**: Permitir trafego entre NLB → ALB → Pods

### Fluxo de Provisionamento

```
1. Criar NLB interno (modulo nlb)
       │
       ▼
2. Criar ALB interno (modulo alb)
       │
       ▼
3. Configurar NLB → ALB (target group)
       │
       ▼
4. Criar VPC Link apontando para NLB
       │
       ▼
5. Configurar API Gateway com connection_type = VPC_LINK
```

### Tempo de Provisionamento

| Recurso | Tempo Estimado |
|---------|----------------|
| VPC Link | 2-5 minutos |
| NLB + Target | 3-5 minutos |

**Nota:** O VPC Link fica no estado `PENDING` ate que o NLB esteja fully provisioned.

---

## Rate Limiting

### Niveis de Throttling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   NIVEL 1: Account Level                                                    │
│   └── Limite padrao AWS: 10.000 req/s por regiao                           │
│                                                                             │
│   NIVEL 2: API/Stage Level (method_settings)                               │
│   └── throttle_burst_limit: 5000                                           │
│   └── throttle_rate_limit: 10000                                           │
│                                                                             │
│   NIVEL 3: Usage Plan Level (se enable_usage_plan = true)                  │
│   └── usage_plan_throttle_burst_limit: 2000                                │
│   └── usage_plan_throttle_rate_limit: 1000                                 │
│   └── usage_plan_quota_limit: 1000000/MONTH                                │
│                                                                             │
│   NIVEL 4: API Key Level                                                    │
│   └── Herda limites do Usage Plan                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Configuracao Recomendada

| Ambiente | Stage Burst | Stage Rate | API Key Burst | API Key Rate | Quota |
|----------|-------------|------------|---------------|--------------|-------|
| **Dev** | 1000 | 2000 | 500 | 200 | 100K/month |
| **Staging** | 5000 | 10000 | 2000 | 1000 | 1M/month |
| **Prod** | 10000 | 20000 | 5000 | 2000 | 10M/month |

### Resposta de Throttling

Quando o limite e atingido:

```json
HTTP/1.1 429 Too Many Requests
{
  "message": "Rate exceeded"
}
```

---

## Logs e Metricas

### Formato de Log

```json
{
  "requestId": "abc123-xyz789",
  "ip": "203.0.113.50",
  "caller": "-",
  "user": "-",
  "requestTime": "15/Jan/2024:10:30:00 +0000",
  "httpMethod": "POST",
  "resourcePath": "/authorize-purchase",
  "status": "200",
  "protocol": "HTTP/1.1",
  "responseLength": "256",
  "latency": "45"
}
```

### Metricas CloudWatch

| Metrica | Descricao | Alarme Sugerido |
|---------|-----------|-----------------|
| `Count` | Total de requests | Baseline |
| `4XXError` | Erros do cliente | > 5% |
| `5XXError` | Erros do servidor | > 1% |
| `Latency` | Latencia (ms) | p95 > 500ms |
| `IntegrationLatency` | Latencia do backend | p95 > 400ms |

### Consultar Logs

```bash
# Via AWS CLI
aws logs filter-log-events \
  --log-group-name "/aws/apigateway/elo-fraud-api-dev" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern '{ $.status = "500" }'
```

---

## Exemplos

### API Simples para Dev

```hcl
module "api_gateway_dev" {
  source = "../../modules/api-gateway"

  project_name = "elo-fraud"
  environment  = "dev"
  api_name     = "elo-fraud-api-dev"

  # VPC Link (obrigatorio)
  nlb_arn      = module.nlb.nlb_arn
  nlb_dns_name = module.nlb.nlb_dns_name
}
```

### API com Rate Limiting para Producao

```hcl
module "api_gateway_prod" {
  source = "../../modules/api-gateway"

  project_name    = "elo-fraud"
  environment     = "prod"
  api_name        = "elo-fraud-api-prod"
  api_description = "API de Autorizacao de Compras Online - Producao"

  # VPC Link (trafego interno)
  nlb_arn      = module.nlb.nlb_arn
  nlb_dns_name = module.nlb.nlb_dns_name

  # Rate limiting (stage level)
  throttle_burst_limit = 10000
  throttle_rate_limit  = 20000

  # Usage Plan com quotas
  enable_usage_plan               = true
  usage_plan_quota_limit          = 10000000  # 10M/mes
  usage_plan_throttle_burst_limit = 5000
  usage_plan_throttle_rate_limit  = 2000

  # API Keys para clientes
  api_keys = {
    "elo-main" = {
      enabled     = true
      description = "Elo main backend"
    }
    "partner-a" = {
      enabled     = true
      description = "Partner A integration"
    }
  }
}
```

---

## Troubleshooting

### Erro: 500 Internal Server Error

**Sintoma:**
```json
{"message": "Internal server error"}
```

**Causas e Solucoes:**

1. **Backend nao acessivel**
   ```bash
   # Verificar se ALB/NLB esta respondendo
   curl -v http://NLB_DNS_NAME/health
   ```

2. **VPC Link nao disponivel**
   ```bash
   # Verificar status do VPC Link
   aws apigateway get-vpc-link --vpc-link-id VPC_LINK_ID
   # Status deve ser AVAILABLE
   ```

3. **Deployment desatualizado**
   ```bash
   # Re-deploy
   terraform apply -target=module.api_gateway
   ```

### Erro: 403 Forbidden

**Sintoma:**
```json
{"message": "Forbidden"}
```

**Causas:**

1. **API Key invalida ou ausente** (se `enable_usage_plan = true`)
   ```bash
   # Adicionar header x-api-key
   curl -H "x-api-key: YOUR_KEY" ...
   ```

2. **API Key nao associada ao Usage Plan**
   - Verificar `aws_api_gateway_usage_plan_key`

3. **Resource policy bloqueando acesso**
   - Verificar se ha restricoes de IP ou VPC

4. **Endpoint privado sem permissao**
   - Verificar VPC endpoint policies

### Erro: 429 Too Many Requests

**Sintoma:**
```json
{"message": "Rate exceeded"}
```

**Solucao:**
```hcl
# Aumentar limites
throttle_burst_limit = 10000
throttle_rate_limit  = 20000
```

### Verificar Configuracao

```bash
# Listar recursos da API
aws apigateway get-resources \
  --rest-api-id API_ID \
  --query 'items[*].[path,id]' \
  --output table

# Verificar integracao
aws apigateway get-integration \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method POST

# Testar endpoint
aws apigateway test-invoke-method \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method POST \
  --body '{"test": true}'
```

---

## Timeouts

### Limites do API Gateway

| Timeout | Valor | Nota |
|---------|-------|------|
| **Integration timeout** | 29 segundos | Maximo do API Gateway |
| **Health check** | 5 segundos | Configurado no modulo |

### Recomendacao

Se o backend demorar mais de 29s, considere:
1. **Otimizar backend** para responder mais rapido
2. **Processamento assincrono** via SQS
3. **AWS AppSync** para timeouts maiores

---

## Headers Adicionados

O modulo configura automaticamente headers de rastreamento:

| Header | Valor | Uso |
|--------|-------|-----|
| `X-Forwarded-For` | IP do cliente | Identificar origem |
| `X-Trace-Id` | Request ID do API Gateway | Rastreamento end-to-end |

---

## Operacoes

### Verificar Status da API

```bash
# Listar REST APIs
aws apigateway get-rest-apis \
  --query 'items[*].[name,id]' \
  --output table

# Detalhes de uma API
aws apigateway get-rest-api \
  --rest-api-id API_ID

# Listar stages
aws apigateway get-stages \
  --rest-api-id API_ID \
  --query 'item[*].[stageName,deploymentId]' \
  --output table
```

### Verificar Recursos e Metodos

```bash
# Listar recursos
aws apigateway get-resources \
  --rest-api-id API_ID \
  --query 'items[*].[path,id]' \
  --output table

# Ver integracao de um metodo
aws apigateway get-integration \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method POST

# Ver configuracao de metodo
aws apigateway get-method \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method POST
```

### Testar Endpoint

```bash
# Via curl (com API Key se enable_usage_plan = true)
curl -X POST https://API_ID.execute-api.us-east-1.amazonaws.com/v1/authorize-purchase \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"transaction_id": "test-123"}'

# Health check (nao requer API Key)
curl https://API_ID.execute-api.us-east-1.amazonaws.com/v1/health

# Test invoke via AWS CLI
aws apigateway test-invoke-method \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method POST \
  --body '{"test": true}'
```

### Gerenciar API Keys

```bash
# Listar API Keys
aws apigateway get-api-keys \
  --include-values \
  --query 'items[*].[name,id,value]' \
  --output table

# Obter valor de uma API Key especifica
terraform output -json api_gateway_api_keys | jq -r '.["elo-backend"]'

# Criar nova API Key (via AWS CLI)
aws apigateway create-api-key \
  --name "elo-fraud-new-key" \
  --enabled

# Associar key ao Usage Plan
aws apigateway create-usage-plan-key \
  --usage-plan-id USAGE_PLAN_ID \
  --key-id API_KEY_ID \
  --key-type API_KEY
```

### Ver Logs e Metricas

```bash
# Logs no CloudWatch
aws logs tail /aws/apigateway/elo-fraud-api-dev --follow

# Metricas de latencia
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=elo-fraud-api-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average,p95

# Contagem de erros 5XX
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name 5XXError \
  --dimensions Name=ApiName,Value=elo-fraud-api-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum
```

---

## Custos Estimados

### Precos API Gateway REST API (sa-east-1)

| Componente | Preco | Nota |
|------------|-------|------|
| **Requests (primeiros 333M)** | $3.50 / milhao | Por mes |
| **Requests (acima 333M)** | $2.80 / milhao | Desconto por volume |
| **Data Transfer Out** | $0.09 / GB | Para internet |
| **Caching (opcional)** | $0.02 - $3.80 / hora | Por tamanho do cache |

### Estimativa Mensal por Ambiente

| Ambiente | Requests/Mes | Data Transfer | Custo Estimado |
|----------|--------------|---------------|----------------|
| **DEV** | 100.000 | 1 GB | ~$0.50 |
| **STAGING** | 1.000.000 | 10 GB | ~$4.50 |
| **PROD** | 10.000.000 | 100 GB | ~$44.00 |

### Custos de VPC Link

| Componente | Preco | Nota |
|------------|-------|------|
| **VPC Link por hora** | $0.01 / hora | ~$7.30/mes |
| **Data processado** | $0.01 / GB | Via VPC Link |

### Otimizacao de Custos

| Estrategia | Economia Potencial |
|------------|-------------------|
| Desabilitar cache (para dados dinamicos) | 100% do custo de cache |
| Usar throttling adequado | Evita custos de pico |
| Regional endpoint (vs Edge) | ~10-20% em latencia/custo |
| Compressao de responses | Reduz data transfer |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **REST API (vs HTTP API)** | Mais recursos (usage plans, API keys, request validation) |
| **Regional endpoint** | Menor latencia para clientes na mesma regiao |
| **VPC Link para ALB interno** | Trafego nunca sai da rede AWS, maior seguranca |
| **Usage Plan com API Key** | Identificacao de clientes e rate limiting por cliente |
| **Stage-level throttling** | Protecao global contra abuso |
| **Throttling 10K req/s** | Protege backend de picos de trafego |
| **Cache desabilitado** | Autorizacao de compra nao deve ser cacheada |
| **Logs habilitados** | Auditoria e troubleshooting |

> **NOTA:** API Keys sao para **identificacao e throttling**, NAO para autenticacao.
> Para autenticacao, use IAM, Cognito ou Lambda Authorizer.

---

## Referencias

### AWS Documentation

- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html)
- [API Gateway VPC Link](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-private-integration.html)
- [Usage Plans and API Keys](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-api-usage-plans.html)
- [API Gateway Throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)

### Terraform Documentation

- [aws_api_gateway_rest_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api)
- [aws_api_gateway_vpc_link](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_vpc_link)
- [aws_api_gateway_usage_plan](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_usage_plan)
- [aws_api_gateway_api_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_api_key)

### Best Practices

- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-basic-concept.html)
- [Securing API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html)

