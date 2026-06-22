# DynamoDB Module

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Modelo de Dados](#modelo-de-dados)
- [Recursos Criados](#recursos-criados)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Operacoes](#operacoes)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo provisiona uma tabela **Amazon DynamoDB** que funciona como **Feature Store** para armazenar as transacoes recentes por cliente, permitindo enriquecimento em tempo real durante o scoring de fraude.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Feature Store** | Armazena historico recente de transacoes por cliente |
| **Enriquecimento Real-time** | Fornece dados para calcular features durante inferencia |
| **Latencia Sub-milissegundo** | Atende SLA de 500ms para scoring de fraude |

### Por que DynamoDB?

| Beneficio | Descricao |
|-----------|-----------|
| **Latencia Single-digit** | Respostas em milissegundos para atender SLA de 500ms |
| **Escalabilidade** | Escala automaticamente com o volume de transacoes |
| **Serverless** | Modo PAY_PER_REQUEST nao requer gerenciamento de capacidade |

---

## Arquitetura

```
                                    Fluxo de Dados
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              ┌─────────────────────┐                           │
│                              │     DynamoDB        │                           │
│                              │  customer_recent_tx │                           │
│                              └─────────────────────┘                           │
│                                        │                                        │
│                                        ▼                                        │
│                             ┌─────────────────┐                                │
│                             │  Primary Key    │                                │
│                             │                 │                                │
│                             │ PK: cardHolder  │                                │
│                             │     Document    │                                │
│                             │ SK: tx_id       │                                │
│                             └─────────────────┘                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                              Integracao com EKS
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                                 ESCRITA                                         │
│   ┌───────────────┐                              ┌───────────────┐             │
│   │  EKS Service  │──── PutItem/UpdateItem ────▶│   DynamoDB    │             │
│   │   (process)   │                              │               │             │
│   └───────────────┘                              │ - Nova tx     │             │
│         │                                        │ - feedback    │             │
│         └── Atualiza com fraud_label             │   (label)     │             │
│                                                  └───────────────┘             │
│                                                                                 │
│                                 LEITURA                                         │
│   ┌───────────────┐                              ┌───────────────┐             │
│   │  EKS Service  │◀──── Query/GetItem ─────────│   DynamoDB    │             │
│   │  (inference)  │                              │               │             │
│   └───────────────┘                              │ - Por doc     │             │
│         │                                        │               │             │
│         └── Enriquece features com historico     │               │             │
│                                                  └───────────────┘             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Modelo de Dados

### Estrutura da Tabela

O DynamoDB e schemaless - apenas as chaves (Partition Key e Sort Key) sao definidas no Terraform. Os demais atributos sao adicionados dinamicamente pela aplicacao.

**Chaves definidas pelo modulo:**

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| `cardHolderDocument` | String (S) | **Partition Key** - Hash do documento do portador |
| `transaction_id` | Number (N) | **Sort Key** - ID unico da transacao |

**Atributos adicionais (definidos pela aplicacao):**

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| `timestamp` | Number (N) | Timestamp da transacao |
| `payload` | String (S) | JSON com dados completos da transacao |

> **Nota**: Os atributos `timestamp` e `payload` nao sao definidos no Terraform. Eles sao adicionados dinamicamente quando a aplicacao insere itens na tabela.

### Design de Chaves

```
┌─────────────────────────────────────────────────────────────────┐
│                       Partition Key                             │
│                    cardHolderDocument                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ "abc123hash"                                             │   │
│  │    ├── tx_id: 1001  { timestamp, payload }              │   │
│  │    ├── tx_id: 1002  { timestamp, payload }              │   │
│  │    ├── tx_id: 1003  { timestamp, payload }              │   │
│  │    └── tx_id: 1004  { timestamp, payload }              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ "def456hash"                                             │   │
│  │    ├── tx_id: 2001  { timestamp, payload }              │   │
│  │    └── tx_id: 2002  { timestamp, payload }              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Padroes de Acesso

| Padrao | Chave/Indice | Query | Descricao |
|--------|--------------|-------|-----------|
| Historico por cliente | Primary Key | `PK = cardHolderDocument` | Ultimas N transacoes de um documento |
| Transacao especifica | Primary Key | `PK = doc AND SK = tx_id` | Uma transacao especifica |

---

## Recursos Criados

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| `this` | `aws_dynamodb_table` | Tabela DynamoDB configuravel |

### Features da Tabela

| Feature | Descricao | Configuravel |
|---------|-----------|--------------|
| **Billing Mode** | PAY_PER_REQUEST (On-Demand) | Nao (fixo) |
| **Server-side Encryption** | Criptografia em repouso (AWS managed key, padrao) | Nao (padrao AWS) |
| **Point-in-Time Recovery** | Backup continuo para recuperacao | Sim (`point_in_time_recovery_enabled`) |
| **Deletion Protection** | Protecao contra delecao acidental | Sim (`deletion_protection_enabled`) |
| **Schema** | Hash key e Range key configuraveis | Sim (variaveis) |

### Modo de Cobranca: PAY_PER_REQUEST (On-Demand)

| Caracteristica | Descricao |
|----------------|-----------|
| **Modelo** | Paga por operacao (leitura/escrita) |
| **Capacidade** | Automatica, sem limites pre-definidos |
| **Scaling** | Instantaneo |
| **Gerenciamento** | Zero configuracao de capacidade |

### Precos (sa-east-1)

| Componente | Preco |
|------------|-------|
| Write Request Unit (WRU) | $1.25 / milhao |
| Read Request Unit (RRU) | $0.25 / milhao |
| Storage (primeiros 25 GB) | Gratuito |
| Storage (acima de 25 GB) | $0.25 / GB / mes |

---

## Uso

### Uso Basico (DEV)

```hcl
module "dynamodb" {
  source = "../../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  # Schema (usando defaults)
  # table_name_suffix = "customer-recent-tx"
  # hash_key          = "cardHolderDocument"
  # hash_key_type     = "S"
  # range_key         = "transaction_id"
  # range_key_type    = "N"

  # Seguranca - DEV (relaxado)
  point_in_time_recovery_enabled = false # Nao necessario em dev
  deletion_protection_enabled    = false # Permite deletar em dev

  tags = var.common_tags
}
```

### Uso para STAGING

```hcl
module "dynamodb" {
  source = "../../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  # Seguranca - STAGING (moderado)
  point_in_time_recovery_enabled = true # Backup continuo habilitado
  deletion_protection_enabled    = false

  tags = var.common_tags
}
```

### Uso para PROD

```hcl
module "dynamodb" {
  source = "../../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  # Seguranca - PROD (maximo)
  point_in_time_recovery_enabled = true  # Backup continuo
  deletion_protection_enabled    = true  # Protege contra delecao

  tags = var.common_tags
}
```

---

## Variaveis

### Obrigatorias

| Variavel | Tipo | Descricao |
|----------|------|-----------|
| `project_name` | `string` | Nome do projeto |
| `environment` | `string` | Ambiente (dev, staging, prod) |

### Configuracao da Tabela

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `table_name_suffix` | `string` | `"customer-recent-tx"` | Sufixo do nome da tabela |
| `hash_key` | `string` | `"cardHolderDocument"` | Nome do partition key |
| `hash_key_type` | `string` | `"S"` | Tipo do partition key (S, N, B) |
| `range_key` | `string` | `"transaction_id"` | Nome do sort key |
| `range_key_type` | `string` | `"N"` | Tipo do sort key (S, N, B) |

### Seguranca e Resiliencia

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `point_in_time_recovery_enabled` | `bool` | `false` | Habilitar backup continuo |
| `deletion_protection_enabled` | `bool` | `false` | Proteger contra delecao acidental |

### Tags

| Variavel | Tipo | Padrao | Descricao |
|----------|------|--------|-----------|
| `tags` | `map(string)` | `{}` | Tags adicionais |

### Configuracao Recomendada por Ambiente

| Variavel | DEV | STAGING | PROD |
|----------|-----|---------|------|
| `point_in_time_recovery_enabled` | `false` | `true` | `true` |
| `deletion_protection_enabled` | `false` | `false` | `true` |

---

## Outputs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `table_id` | `string` | ID da tabela |
| `table_name` | `string` | Nome da tabela |
| `table_arn` | `string` | ARN da tabela |
| `dynamodb_summary` | `object` | Resumo completo da configuracao |

### Estrutura do dynamodb_summary

```hcl
{
  table_name                     = "elo-fraud-customer-recent-tx-dev"
  table_arn                      = "arn:aws:dynamodb:..."
  hash_key                       = "cardHolderDocument"
  range_key                      = "transaction_id"
  point_in_time_recovery_enabled = false
  deletion_protection_enabled    = false
}
```

### Exemplo de Uso dos Outputs

```hcl
# Em outro modulo
resource "aws_iam_policy" "dynamodb_access" {
  name = "dynamodb-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = module.dynamodb.table_arn
      }
    ]
  })
}
```

---

## Operacoes

### Consultar Item por Documento

```bash
aws dynamodb query \
  --table-name elo-fraud-customer-recent-tx-staging \
  --key-condition-expression "cardHolderDocument = :doc" \
  --expression-attribute-values '{":doc":{"S":"abc123hash"}}' \
  --scan-index-forward false \
  --limit 10 \
  --region sa-east-1
```

### Inserir Item

```bash
aws dynamodb put-item \
  --table-name elo-fraud-customer-recent-tx-staging \
  --item '{
    "cardHolderDocument": {"S": "abc123hash"},
    "transaction_id": {"N": "1001"},
    "timestamp": {"N": "1705315800"},
    "payload": {"S": "{\"amount\": 150.00, \"mcc\": \"5411\"}"}
  }' \
  --region sa-east-1
```

### Verificar Metricas

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=elo-fraud-customer-recent-tx-staging \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region sa-east-1
```

### Listar Tabelas

```bash
aws dynamodb list-tables --region sa-east-1
```

---

## Troubleshooting

### Erro: Hot Partition

**Sintoma**: Throttling mesmo com On-Demand.

**Causa**: Partition key mal distribuida (muitos acessos na mesma particao).

**Solucao**: Verificar distribuicao de chaves:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=elo-fraud-customer-recent-tx-staging \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum \
  --region sa-east-1
```

---

### Erro: Item Size Exceeded

**Sintoma**:
```
ValidationException: Item size has exceeded the maximum allowed size
```

**Causa**: Item maior que 400KB.

**Solucao**: Reduzir tamanho do item ou usar S3 para dados grandes:
```python
import boto3
import json

# Item grande -> S3
s3 = boto3.client('s3')
s3.put_object(
    Bucket='data-bucket',
    Key=f'items/{doc}/{tx_id}.json',
    Body=json.dumps(large_data)
)

# DynamoDB -> referencia
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('elo-fraud-customer-recent-tx-staging')
table.put_item(Item={
    'cardHolderDocument': doc,
    'transaction_id': tx_id,
    's3_reference': f's3://data-bucket/items/{doc}/{tx_id}.json'
})
```

---

### Verificar Saude da Tabela

```bash
# Descrever tabela completa
aws dynamodb describe-table \
  --table-name elo-fraud-customer-recent-tx-staging \
  --region sa-east-1

# Contar itens (aproximado)
aws dynamodb describe-table \
  --table-name elo-fraud-customer-recent-tx-staging \
  --query 'Table.ItemCount' \
  --region sa-east-1
```

---

## Custos Estimados

### Precos DynamoDB On-Demand (sa-east-1)

| Componente | Preco |
|------------|-------|
| Write Request Unit (WRU) | $1.25 / milhao |
| Read Request Unit (RRU) | $0.25 / milhao |
| Storage (primeiros 25 GB) | Gratuito |
| Storage (acima de 25 GB) | $0.25 / GB / mes |

### Estimativa Mensal por Ambiente

| Ambiente | Operacoes/mes | Storage | Custo Estimado |
|----------|---------------|---------|----------------|
| **DEV** | ~100K | 1 GB | ~$0.15 |
| **STAGING** | ~1M | 10 GB | ~$1.50 |
| **PROD** | ~100M | 100 GB | ~$150 |

### Custos Adicionais

| Feature | Preco | Nota |
|---------|-------|------|
| **Streams** | $0.02 / 100K reads | Para CDC |
| **Backup (On-Demand)** | $0.10 / GB | Snapshot |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Partition Key por documento** | Distribui dados uniformemente e suporta o padrao de acesso principal |
| **Sort Key por transaction_id** | Permite ordenacao cronologica e queries de range |
| **PAY_PER_REQUEST** | Escala automaticamente, zero gerenciamento de capacidade, custo zero sem trafego |

---

## Referencias

- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Partition Key Design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)
- [On-Demand Capacity Mode](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html#HowItWorks.OnDemand)
