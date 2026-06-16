# Bedrock Agent Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Seguranca](#seguranca)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Integracao com Athena](#integracao-com-athena)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona a **IAM Role** necessaria para **Amazon Bedrock Agents** com permissoes para consultar dados no Data Lake via **Amazon Athena**.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Agentes de IA** | Habilita agentes Bedrock a responder perguntas sobre dados de fraude |
| **Consultas SQL** | Permite execucao de queries Athena sobre tabelas do Glue Catalog |
| **Acesso a Modelos** | Permite uso de modelos Claude, Titan, etc. via Bedrock |
| **Funcoes Auxiliares** | Habilita invocacao de Lambdas para acoes complementares |

### Caso de Uso Principal

```
Usuario: "Quantas transacoes fraudulentas ocorreram ontem?"
    │
    ▼
Bedrock Agent (Claude)
    │
    ├── 1. Interpreta pergunta em linguagem natural
    ├── 2. Gera query SQL apropriada
    ├── 3. Executa via Athena
    └── 4. Retorna resposta formatada
```

---

## Arquitetura

```
                                    AWS Account
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                     Amazon Bedrock Agent                            │  │
│   │                                                                      │  │
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │  │
│   │   │   Claude 3   │    │    Titan     │    │   Outros     │         │  │
│   │   │   Sonnet     │    │  Embeddings  │    │   Modelos    │         │  │
│   │   └──────────────┘    └──────────────┘    └──────────────┘         │  │
│   │                                                                      │  │
│   │   Assume Role: {project}-bedrock-agent-{env}                        │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              │ IAM Role                                     │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                         IAM Policies                                 │  │
│   │                                                                      │  │
│   │   ┌────────────────────┐  ┌────────────────────┐                    │  │
│   │   │ AmazonAthenaFull   │  │ AmazonS3Full       │                    │  │
│   │   │ Access             │  │ Access             │                    │  │
│   │   │                    │  │                    │                    │  │
│   │   │ - StartQuery       │  │ - GetObject        │                    │  │
│   │   │ - GetQueryResults  │  │ - PutObject        │                    │  │
│   │   │ - GetWorkgroup     │  │ - ListBucket       │                    │  │
│   │   └────────────────────┘  └────────────────────┘                    │  │
│   │                                                                      │  │
│   │   ┌────────────────────┐  ┌────────────────────┐                    │  │
│   │   │ AmazonBedrockFull  │  │ AWSLambda_Full     │                    │  │
│   │   │ Access             │  │ Access             │                    │  │
│   │   │                    │  │                    │                    │  │
│   │   │ - InvokeModel      │  │ - InvokeFunction   │                    │  │
│   │   │ - ListModels       │  │ - GetFunction      │                    │  │
│   │   │ - GetAgent         │  │                    │                    │  │
│   │   └────────────────────┘  └────────────────────┘                    │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│              ┌───────────────┼───────────────┐                             │
│              ▼               ▼               ▼                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│   │    Athena    │  │      S3      │  │    Lambda    │                    │
│   │              │  │  Data Lake   │  │   Actions    │                    │
│   │  - Queries   │  │              │  │              │                    │
│   │  - Workgroup │  │  - Parquet   │  │  - Alertas   │                    │
│   │              │  │  - Delta     │  │  - Notif.    │                    │
│   └──────────────┘  └──────────────┘  └──────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `bedrock_agent` | `aws_iam_role` | IAM Role para Bedrock Agents |
| `athena` | `aws_iam_role_policy_attachment` | Policy de acesso ao Athena |
| `s3` | `aws_iam_role_policy_attachment` | Policy de acesso ao S3 |
| `bedrock` | `aws_iam_role_policy_attachment` | Policy de acesso ao Bedrock |
| `lambda` | `aws_iam_role_policy_attachment` | Policy de acesso ao Lambda |

### Policies Anexadas

| Policy ARN | Proposito |
|------------|-----------|
| `arn:aws:iam::aws:policy/AmazonAthenaFullAccess` | Executar queries SQL no Athena |
| `arn:aws:iam::aws:policy/AmazonS3FullAccess` | Acessar dados no Data Lake |
| `arn:aws:iam::aws:policy/AmazonBedrockFullAccess` | Invocar modelos de IA |
| `arn:aws:iam::aws:policy/AWSLambda_FullAccess` | Invocar funcoes auxiliares |

---

## Seguranca

### Trust Policy

A IAM Role utiliza uma **Trust Policy** restritiva que garante que apenas Bedrock Agents da propria conta podem assumir a role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "<ACCOUNT_ID>"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:<REGION>:<ACCOUNT_ID>:agent/*"
        }
      }
    }
  ]
}
```

### Condicoes de Seguranca

| Condicao | Descricao |
|----------|-----------|
| `aws:SourceAccount` | Restringe para a propria conta AWS |
| `aws:SourceArn` | Restringe apenas para recursos do tipo `agent/*` |

### Nota sobre SCP

> **Importante**: Tags em IAM Roles foram removidas devido a SCP (Service Control Policy) que bloqueia `iam:TagRole`. Quando o SCP for ajustado, as tags podem ser habilitadas.

---

## Uso

### Uso Basico

```hcl
module "bedrock_agent" {
  source = "../../modules/bedrock-agent"

  project_name = "elo-fraud"
  environment  = "staging"
}
```

### Uso Completo

```hcl
module "bedrock_agent" {
  source = "../../modules/bedrock-agent"

  project_name = "elo-fraud"
  environment  = "staging"

  tags = {
    Project     = "elo-fraud"
    Environment = "staging"
    ManagedBy   = "terraform"
  }
}

# Usar o ARN da role ao criar o Bedrock Agent no console ou via CLI
output "bedrock_agent_role" {
  value = module.bedrock_agent.role_arn
}
```

### Criar Bedrock Agent via AWS CLI

Apos aplicar o Terraform, use o ARN da role para criar o agente:

```bash
# Obter ARN da role
ROLE_ARN=$(terraform output -raw bedrock_agent_role)

# Criar agente Bedrock
aws bedrock-agent create-agent \
  --agent-name "elo-fraud-analyst" \
  --agent-resource-role-arn "$ROLE_ARN" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "Voce e um analista de fraudes. Responda perguntas sobre transacoes usando consultas SQL no Athena." \
  --region sa-east-1
```

---

## Variaveis

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `project_name` | `string` | Sim | - | Nome do projeto (usado no nome da role) |
| `environment` | `string` | Sim | - | Ambiente (dev, staging, prod) |
| `tags` | `map(string)` | Nao | `{}` | Tags para os recursos |

### Nomenclatura da Role

A role e nomeada seguindo o padrao:

```
{project_name}-bedrock-agent-{environment}
```

**Exemplo**: `elo-fraud-bedrock-agent-staging`

---

## Outputs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `role_arn` | `string` | ARN completo da IAM Role |
| `role_name` | `string` | Nome da IAM Role |

### Exemplo de Uso dos Outputs

```hcl
# Em outro modulo ou stack
resource "aws_bedrock_agent" "fraud_analyst" {
  agent_name              = "fraud-analyst"
  agent_resource_role_arn = module.bedrock_agent.role_arn
  foundation_model        = "anthropic.claude-3-sonnet-20240229-v1:0"
  # ...
}
```

---

## Integracao com Athena

### Fluxo de Consulta

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Usuario   │────▶│   Bedrock   │────▶│   Athena    │────▶│     S3      │
│             │     │    Agent    │     │             │     │  Data Lake  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      │  "Quantas        │                   │                   │
      │   fraudes        │  SELECT COUNT(*)  │                   │
      │   ontem?"        │  FROM fraud       │   Leitura         │
      │                  │  WHERE date=...   │   Parquet/Delta   │
      │                  │                   │                   │
      │◀─────────────────│◀──────────────────│◀──────────────────│
      │  "Foram 127      │   127             │   Dados           │
      │   fraudes"       │                   │                   │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Tabelas Disponiveis

O Bedrock Agent pode consultar as seguintes tabelas via Athena:

| Tabela | Database | Descricao |
|--------|----------|-----------|
| `transaction_results` | `elo_fraud_*` | Resultados de inferencia (Delta Lake) |
| `inference_logs` | `elo_fraud_*` | Logs de predicao (JSON particionado) |

### Exemplos de Consultas

O agente pode gerar automaticamente queries como:

```sql
-- Total de transacoes por dia
SELECT date, COUNT(*) as total
FROM elo_fraud_staging.transaction_results
GROUP BY date
ORDER BY date DESC
LIMIT 7;

-- Distribuicao de scores de fraude
SELECT
  CASE
    WHEN fraud_score < 0.3 THEN 'Baixo'
    WHEN fraud_score < 0.7 THEN 'Medio'
    ELSE 'Alto'
  END as risco,
  COUNT(*) as quantidade
FROM elo_fraud_staging.inference_logs
WHERE year = '2024' AND month = '01'
GROUP BY 1;
```

---

## Troubleshooting

### Erro: Access Denied ao assumir role

**Sintoma**:
```
AccessDeniedException: User is not authorized to perform: sts:AssumeRole
```

**Causa**: O Bedrock Agent nao esta na mesma conta ou regiao especificada na Trust Policy.

**Solucao**: Verificar se o agente esta na mesma conta AWS:

```bash
# Verificar conta atual
aws sts get-caller-identity

# Verificar configuracao da role
aws iam get-role \
  --role-name elo-fraud-bedrock-agent-staging \
  --query 'Role.AssumeRolePolicyDocument'
```

---

### Erro: Athena Query Failed

**Sintoma**:
```
AthenaQueryException: Query failed with error: Access Denied
```

**Causa**: A role nao tem permissao para acessar o bucket S3 ou workgroup Athena.

**Solucao**: Verificar policies anexadas:

```bash
aws iam list-attached-role-policies \
  --role-name elo-fraud-bedrock-agent-staging
```

---

### Erro: Model Access Denied

**Sintoma**:
```
AccessDeniedException: You don't have access to the model
```

**Causa**: O modelo Bedrock nao foi habilitado na conta.

**Solucao**: Habilitar acesso ao modelo no console Bedrock:

1. Acessar **Amazon Bedrock** > **Model access**
2. Solicitar acesso aos modelos desejados (Claude, Titan, etc.)
3. Aguardar aprovacao

---

### Verificar Permissoes da Role

```bash
# Listar policies anexadas
aws iam list-attached-role-policies \
  --role-name elo-fraud-bedrock-agent-staging

# Simular permissao especifica
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::888577064416:role/elo-fraud-bedrock-agent-staging \
  --action-names athena:StartQueryExecution \
  --resource-arns "arn:aws:athena:sa-east-1:888577064416:workgroup/*"
```

---

### Testar Conectividade Athena

```bash
# Executar query de teste
aws athena start-query-execution \
  --query-string "SELECT 1" \
  --work-group primary \
  --region sa-east-1

# Verificar resultado
aws athena get-query-results \
  --query-execution-id <QUERY_ID>
```

---

## Melhores Praticas

### 1. Least Privilege (Futuro)

Considerar restringir as policies para acesso minimo necessario:

```hcl
# Exemplo de policy customizada mais restritiva
resource "aws_iam_policy" "bedrock_agent_custom" {
  name = "${var.project_name}-bedrock-agent-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]
        Resource = [
          "arn:aws:athena:${local.region}:${local.account_id}:workgroup/${var.athena_workgroup}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.data_lake_bucket}",
          "arn:aws:s3:::${var.data_lake_bucket}/*"
        ]
      }
    ]
  })
}
```

### 2. Monitoramento

Configurar CloudWatch alarms para monitorar uso do agente:

```bash
# Metricas disponiveis
aws cloudwatch list-metrics \
  --namespace AWS/Bedrock \
  --region sa-east-1
```

### 3. Logging

Habilitar logging de invocacoes no Bedrock Agent para auditoria.

---

## Operacoes

### Gerenciar Agent

```bash
# Listar agents
aws bedrock-agent list-agents \
  --region sa-east-1 \
  --output table

# Detalhes do agent
aws bedrock-agent get-agent \
  --agent-id "AGENT_ID" \
  --region sa-east-1

# Ver alias do agent
aws bedrock-agent list-agent-aliases \
  --agent-id "AGENT_ID" \
  --region sa-east-1
```

### Invocar Agent

```bash
# Invocar agent (via CLI)
aws bedrock-agent-runtime invoke-agent \
  --agent-id "AGENT_ID" \
  --agent-alias-id "ALIAS_ID" \
  --session-id "session-$(date +%s)" \
  --input-text "Quantas transacoes de fraude tivemos ontem?" \
  --region sa-east-1

# Exemplo com Python
python3 << 'EOF'
import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='sa-east-1')

response = client.invoke_agent(
    agentId='AGENT_ID',
    agentAliasId='ALIAS_ID',
    sessionId='test-session',
    inputText='Qual o total de transacoes processadas hoje?'
)

for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode())
EOF
```

### Gerenciar Knowledge Base

```bash
# Listar knowledge bases
aws bedrock-agent list-knowledge-bases \
  --region sa-east-1

# Sincronizar knowledge base
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id "KB_ID" \
  --data-source-id "DS_ID" \
  --region sa-east-1

# Ver status do ingestion
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id "KB_ID" \
  --data-source-id "DS_ID" \
  --ingestion-job-id "JOB_ID" \
  --region sa-east-1
```

### Metricas e Monitoramento

```bash
# Metricas de invocacao
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Invocations \
  --dimensions Name=AgentId,Value=AGENT_ID \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum

# Latencia
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationLatency \
  --dimensions Name=AgentId,Value=AGENT_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average,p95
```

---

## Custos Estimados

### Precos Bedrock Agents (sa-east-1)

| Componente | Preco | Nota |
|------------|-------|------|
| **Claude 3 Haiku (Input)** | $0.00025 / 1K tokens | Modelo mais economico |
| **Claude 3 Haiku (Output)** | $0.00125 / 1K tokens | - |
| **Claude 3 Sonnet (Input)** | $0.003 / 1K tokens | Modelo balanceado |
| **Claude 3 Sonnet (Output)** | $0.015 / 1K tokens | - |
| **Knowledge Base (Titan Embeddings)** | $0.0001 / 1K tokens | Para RAG |

### Estimativa Mensal por Ambiente

| Ambiente | Invocacoes/Dia | Tokens/Invocacao | Modelo | Custo Estimado |
|----------|----------------|------------------|--------|----------------|
| **DEV** | 50 | 2.000 | Haiku | ~$5.00 |
| **STAGING** | 200 | 3.000 | Haiku | ~$25.00 |
| **PROD** | 1.000 | 4.000 | Sonnet | ~$250.00 |

### Custos Adicionais

| Componente | Preco | Nota |
|------------|-------|------|
| **Athena queries (pelo agent)** | $5 / TB | Dados escaneados |
| **S3 storage (knowledge base)** | $0.023 / GB | Documentos indexados |
| **OpenSearch Serverless (RAG)** | $0.24 / OCU / hora | Se usar vector store |

### Otimizacao de Custos

| Estrategia | Economia Potencial |
|------------|-------------------|
| Usar Haiku para queries simples | ~90% vs Sonnet |
| Limitar tokens de contexto | Proporcional |
| Cache de respostas frequentes | ~50% em invocacoes repetidas |
| Filtrar queries irrelevantes | Evita custos desnecessarios |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Claude 3 Haiku por padrao** | Melhor custo-beneficio para queries de dados |
| **Integracao com Athena** | Permite queries SQL em linguagem natural |
| **Sem Knowledge Base inicial** | Simplifica MVP, adicionar conforme necessidade |
| **IAM Role dedicada** | Principio de menor privilegio |
| **Session ID por request** | Isola conversas, evita vazamento de contexto |
| **Action Group para Athena** | Permite o agent executar queries SQL |

---

## Referencias

- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [IAM Roles for Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-permissions.html)
- [Athena Integration](https://docs.aws.amazon.com/athena/latest/ug/querying.html)
