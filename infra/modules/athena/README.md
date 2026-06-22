# Modulo Athena

## Sumario

- [Visao Geral](#visao-geral)
- [Arquitetura](#arquitetura)
- [Recursos Criados](#recursos-criados)
- [Tabelas](#tabelas)
- [Uso](#uso)
- [Variaveis](#variaveis)
- [Outputs](#outputs)
- [Partition Projection](#partition-projection)
- [Exemplos de Queries](#exemplos-de-queries)
- [Controle de Custos](#controle-de-custos)
- [Integracao com BI](#integracao-com-bi)
- [Troubleshooting](#troubleshooting)

---

## Visao Geral

Este modulo configura o **Amazon Athena** para consultas SQL sobre dados de fraude armazenados no S3, permitindo analises ad-hoc e integracao com ferramentas de BI.

### Proposito

| Funcao | Descricao |
|--------|-----------|
| **Analytics** | Consultas SQL sobre dados historicos de transacoes |
| **Monitoramento ML** | Analise de logs de inferencia do modelo |
| **BI Integration** | Conexao com QuickSight, Tableau, etc. |
| **Ad-hoc Analysis** | Investigacao de fraudes e comportamentos |

### Caracteristicas Principais

| Caracteristica | Valor | Descricao |
|----------------|-------|-----------|
| **Tipo** | Serverless | Sem gerenciamento de infraestrutura |
| **Preco** | $5/TB scanned | Paga apenas pelo uso |
| **Tabelas** | 2 | transaction_results, inference_logs |
| **Partition Projection** | Habilitado | Descoberta automatica de particoes |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              FLUXO DE DADOS                                 │
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │ SageMaker/Spark │                                                       │
│   │   Pipeline      │──────┐                                                │
│   └─────────────────┘      │                                                │
│                            │  Delta Lake (Parquet)                          │
│                            ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                          S3 Bucket (Source)                          │  │
│   │                                                                      │  │
│   │   ├── transaction-results/        (Delta Lake - Parquet)             │  │
│   │   │   └── _delta_log/                                                │  │
│   │   │   └── part-*.parquet                                            │  │
│   │   │                                                                  │  │
│   │   └── inference_logs/             (JSON - Partitioned)               │  │
│   │       └── year=2024/                                                 │  │
│   │           └── month=01/                                              │  │
│   │               └── day=15/                                            │  │
│   │                   └── hour=10/                                       │  │
│   │                       └── *.json                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            │  Glue Catalog                                  │
│                            ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                          Glue Database                               │  │
│   │                       elo_fraud_dev_db                               │  │
│   │                                                                      │  │
│   │   ┌─────────────────────┐    ┌─────────────────────┐               │  │
│   │   │  transaction_results│    │   inference_logs    │               │  │
│   │   │  (Delta Lake)       │    │   (JSON + Partition │               │  │
│   │   │                     │    │    Projection)      │               │  │
│   │   │  - 19 colunas       │    │  - 71 colunas       │               │  │
│   │   │  - Sem particoes    │    │  - 4 particoes      │               │  │
│   │   └─────────────────────┘    └─────────────────────┘               │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            │  SQL Queries                                   │
│                            ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                          Athena Workgroup                            │  │
│   │                                                                      │  │
│   │   - Limite: 10 GB/query                                             │  │
│   │   - Resultados: s3://.../results/                                    │  │
│   │   - Metricas: CloudWatch                                            │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                          Consumidores                                │  │
│   │                                                                      │  │
│   │   QuickSight  │  Jupyter  │  Data Scientists  │  BI Tools           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recursos Criados

### AWS Resources

| Recurso | Tipo | Descricao |
|---------|------|-----------|
| **S3 Bucket** | `aws_s3_bucket` | Armazena resultados das queries |
| **S3 Encryption** | `aws_s3_bucket_server_side_encryption_configuration` | Criptografia SSE-S3 (AES256) |
| **Glue Database** | `aws_glue_catalog_database` | Catalogo de metadados |
| **Glue Table (transaction_results)** | `aws_glue_catalog_table` | Dados Delta Lake |
| **Glue Table (inference_logs)** | `aws_glue_catalog_table` | Logs de inferencia |
| **Athena Workgroup** | `aws_athena_workgroup` | Configuracoes de execucao |

### Diagrama de Recursos

```
aws_glue_catalog_database.main
    │
    ├── aws_glue_catalog_table.transaction_results
    │       └── Delta Lake (Parquet)
    │
    └── aws_glue_catalog_table.inference_logs
            └── JSON + Partition Projection

aws_athena_workgroup.main
    │
    └── aws_s3_bucket.athena_results
            │
            └── aws_s3_bucket_server_side_encryption_configuration.athena_results
                    └── AES256 (SSE-S3)
```

---

## Tabelas

### transaction_results (Delta Lake)

Tabela principal com dados transformados de transacoes e confirmacao de fraude (TE40).

| Atributo | Valor |
|----------|-------|
| **Formato** | Delta Lake (Parquet) |
| **Particoes** | Nenhuma (gerenciado pelo Delta) |
| **Fonte** | Pipeline Spark/SageMaker |
| **Uso** | Treinamento ML, Analytics |

#### Schema Completo (19 colunas)

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `transaction_id` | string | ID unico da transacao |
| `score` | double | Score de fraude (0-1) |
| `fraud_label` | bigint | Label de fraude (0/1) |
| `amount` | double | Valor da transacao |
| `cardholderdocument` | string | Documento do portador |
| `dt_transaction_datetime` | string | Data/hora da transacao |
| `dataset_flag` | string | Flag de dataset (train/test) |
| `enr_card_bank` | string | Banco emissor |
| `enr_card_type` | string | Tipo de cartao |
| `enr_device_os` | string | Sistema operacional do dispositivo |
| `enr_user_doc_id` | string | ID do documento do usuario |
| `cd_merchant_country` | string | Pais do comerciante |
| `cd_merchant_category_code` | string | MCC do comerciante |
| `cd_browser_time_zone` | string | Fuso horario do browser |
| `cd_device_channel` | string | Canal do dispositivo |
| `nm_browser_language` | string | Idioma do browser |
| `nm_cardholder_bill_addr_country` | string | Pais do endereco de cobranca |
| `nm_cardholder_bill_addr_state` | string | Estado do endereco de cobranca |
| `nm_merchant_country_name` | string | Nome do pais do comerciante |

### inference_logs (JSON)

Logs de inferencia do modelo para monitoramento e analise de performance.

| Atributo | Valor |
|----------|-------|
| **Formato** | JSON |
| **Particoes** | year, month, day, hour |
| **Partition Projection** | Habilitado |
| **Fonte** | Kinesis Firehose |
| **Uso** | Monitoramento ML, Debugging |

#### Particoes

| Particao | Tipo | Range |
|----------|------|-------|
| `year` | int | 2024-2030 |
| `month` | int | 1-12 |
| `day` | int | 1-31 |
| `hour` | int | 0-23 |

#### Categorias de Colunas (71)

| Categoria | Exemplos |
|-----------|----------|
| **Identificacao** | transaction_id, score, fraud_label, amount |
| **Dispositivo** | cd_device_channel, enr_device_os, nm_browser_language |
| **Merchant** | cd_merchant_category_code, cd_merchant_country |
| **Endereco** | nm_cardholder_bill_addr_state, in_addr_match_indicator |
| **Cartao** | enr_card_bank, enr_card_type, nu_issuer_bin |
| **3DS** | nm_protocol, cd_transaction_status, cd_eci |
| **Features Usuario** | feat_user_tx_count_total, feat_user_avg_amount_10 |
| **Features Fraude** | feat_user_fraud_count_hist, feat_merchant_has_fraud_hist |
| **Features Tempo** | feat_purchase_weekday, feat_transaction_time_bin |

---

## Uso

### Exemplo Basico

```hcl
module "athena" {
  source = "../../modules/athena"

  project_name       = "elo-fraud"
  environment        = "dev"
  source_bucket_name = module.foundation.s3_processed_bucket_id
}
```

### Exemplo Completo

```hcl
module "athena" {
  source = "../../modules/athena"

  # Identificacao
  project_name = "elo-fraud"
  environment  = "dev"

  # Fonte de dados
  source_bucket_name    = module.foundation.s3_processed_bucket_id
  source_prefix         = "transaction-results"
  inference_logs_prefix = "inference_logs"

  # Controle de custos
  bytes_scanned_limit = 10737418240  # 10 GB

  # Cleanup (apenas dev)
  force_destroy = true

  # Tags
  tags = {
    Team    = "data-science"
    Purpose = "analytics"
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

### Fonte de Dados

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `source_bucket_name` | string | Sim | - | Bucket S3 com dados |
| `source_prefix` | string | Nao | `"transaction-results"` | Prefixo Delta Lake |
| `inference_logs_prefix` | string | Nao | `"inference_logs"` | Prefixo logs inferencia |

### Configuracao

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `bytes_scanned_limit` | number | Nao | `10737418240` | Limite por query (10 GB) |
| `force_destroy` | bool | Nao | `false` | Permite deletar bucket com objetos |

### Tags

| Variavel | Tipo | Obrigatorio | Padrao | Descricao |
|----------|------|-------------|--------|-----------|
| `tags` | map(string) | Nao | `{}` | Tags adicionais |

---

## Outputs

| Output | Tipo | Descricao |
|--------|------|-----------|
| `database_name` | string | Nome do Glue Database |
| `table_name` | string | Nome da tabela transaction_results |
| `inference_logs_table_name` | string | Nome da tabela inference_logs |
| `workgroup_name` | string | Nome do Athena Workgroup |
| `results_bucket_name` | string | Bucket para resultados |
| `results_bucket_arn` | string | ARN do bucket de resultados |
| `connection_info` | object | Objeto com info de conexao |

---

## Partition Projection

### O que e Partition Projection?

Partition Projection e um recurso do Athena que calcula particoes dinamicamente em vez de armazena-las no Glue Catalog. Isso elimina a necessidade de `MSCK REPAIR TABLE` ou Glue Crawlers.

### Como Funciona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   SEM Partition Projection:                                                 │
│                                                                             │
│   1. Firehose grava dados em S3                                            │
│   2. Crawler detecta novas particoes (agendado, pode demorar)              │
│   3. MSCK REPAIR TABLE atualiza particoes                                  │
│   4. Query pode executar                                                    │
│                                                                             │
│   COM Partition Projection:                                                 │
│                                                                             │
│   1. Firehose grava dados em S3                                            │
│   2. Query executa imediatamente (particoes calculadas on-the-fly)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Configuracao no Modulo

```hcl
parameters = {
  "projection.enabled"        = "true"
  "projection.year.type"      = "integer"
  "projection.year.range"     = "2024,2030"
  "projection.year.digits"    = "4"
  "projection.month.type"     = "integer"
  "projection.month.range"    = "1,12"
  "projection.month.digits"   = "2"  # Zero-padding: 01, 02, ...
  "projection.day.type"       = "integer"
  "projection.day.range"      = "1,31"
  "projection.day.digits"     = "2"
  "projection.hour.type"      = "integer"
  "projection.hour.range"     = "0,23"
  "projection.hour.digits"    = "2"
  "storage.location.template" = "s3://bucket/prefix/year=${year}/month=${month}/day=${day}/hour=${hour}/"
}
```

### Vantagens

| Aspecto | Sem Projection | Com Projection |
|---------|----------------|----------------|
| **Nova particao disponivel** | Minutos/horas | Imediato |
| **Custo adicional** | Crawler ($) | $0 |
| **Manutencao** | MSCK REPAIR | Nenhuma |
| **Limite de particoes** | ~10M | Ilimitado |

---

## Exemplos de Queries

### Consultar Transacoes Recentes

```sql
-- Transacoes do ultimo dia
SELECT
    transaction_id,
    amount,
    score,
    fraud_label,
    dt_transaction_datetime
FROM elo_fraud_dev_db.transaction_results
WHERE dataset_flag = 'test'
ORDER BY dt_transaction_datetime DESC
LIMIT 100;
```

### Analise de Fraude por Merchant

```sql
-- Taxa de fraude por categoria de merchant
SELECT
    cd_merchant_category_code,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN fraud_label = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(100.0 * SUM(CASE WHEN fraud_label = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as fraud_rate
FROM elo_fraud_dev_db.transaction_results
GROUP BY cd_merchant_category_code
HAVING COUNT(*) > 100
ORDER BY fraud_rate DESC;
```

### Consultar Inference Logs (com Partition Projection)

```sql
-- Logs de inferencia das ultimas 24 horas
SELECT
    transaction_id,
    score,
    amount,
    enr_card_bank,
    feat_user_tx_count_total
FROM elo_fraud_dev_db.inference_logs
WHERE year = 2024
  AND month = 1
  AND day = 15
ORDER BY score DESC
LIMIT 100;
```

### Monitoramento de Performance do Modelo

```sql
-- Distribuicao de scores por hora
SELECT
    hour,
    COUNT(*) as total,
    AVG(score) as avg_score,
    APPROX_PERCENTILE(score, 0.5) as median_score,
    APPROX_PERCENTILE(score, 0.95) as p95_score
FROM elo_fraud_dev_db.inference_logs
WHERE year = 2024 AND month = 1 AND day = 15
GROUP BY hour
ORDER BY hour;
```

### Analise de Features

```sql
-- Correlacao entre features e fraude
SELECT
    feat_user_has_fraud_history,
    COUNT(*) as total,
    AVG(score) as avg_score,
    SUM(CASE WHEN fraud_label = 1 THEN 1 ELSE 0 END) as fraud_count
FROM elo_fraud_dev_db.inference_logs
WHERE year = 2024 AND month = 1
GROUP BY feat_user_has_fraud_history;
```

---

## Controle de Custos

### Limites Configurados

| Configuracao | Valor | Descricao |
|--------------|-------|-----------|
| **bytes_scanned_cutoff** | 10 GB | Limite por query |
| **Resultado** | Query falha | Se exceder limite |

### Estimativa de Custos

| Cenario | Dados Escaneados | Custo |
|---------|------------------|-------|
| Query pequena (1 dia) | ~100 MB | ~$0.0005 |
| Query media (1 mes) | ~3 GB | ~$0.015 |
| Query grande (1 ano) | ~36 GB | Bloqueada (>10GB) |

### Boas Praticas

```sql
-- BOM: Usar filtros de particao
SELECT * FROM inference_logs
WHERE year = 2024 AND month = 1 AND day = 15;  -- Escaneia ~100MB

-- RUIM: Scan completo da tabela
SELECT * FROM inference_logs;  -- Escaneia tudo!

-- BOM: Selecionar colunas especificas
SELECT transaction_id, score FROM inference_logs
WHERE year = 2024;

-- RUIM: SELECT *
SELECT * FROM inference_logs WHERE year = 2024;
```

### Monitoramento

```bash
# Ver metricas do workgroup
aws athena get-work-group \
  --work-group elo-fraud-athena-workgroup-dev \
  --query 'WorkGroup.Configuration.BytesScannedCutoffPerQuery'

# Historico de queries
aws athena list-query-executions \
  --work-group elo-fraud-athena-workgroup-dev
```

---

## Integracao com BI

### Amazon QuickSight

```
1. QuickSight Console > Datasets > New Dataset
2. Selecionar "Athena"
3. Data source name: elo-fraud-athena
4. Workgroup: elo-fraud-athena-workgroup-dev
5. Database: elo_fraud_dev_db
6. Table: transaction_results ou inference_logs
```

### JDBC/ODBC

```
Driver: Simba Athena JDBC
Host: athena.us-east-1.amazonaws.com
Port: 443
Database: elo_fraud_dev_db
Workgroup: elo-fraud-athena-workgroup-dev
S3 Output: s3://elo-fraud-athena-results-dev-{account}/results/
```

### Python (boto3)

```python
import boto3

athena = boto3.client('athena')

response = athena.start_query_execution(
    QueryString='SELECT * FROM transaction_results LIMIT 10',
    QueryExecutionContext={
        'Database': 'elo_fraud_dev_db'
    },
    WorkGroup='elo-fraud-athena-workgroup-dev'
)

query_execution_id = response['QueryExecutionId']
```

---

## Troubleshooting

### Erro: HIVE_PARTITION_SCHEMA_MISMATCH

**Sintoma:**
```
HIVE_PARTITION_SCHEMA_MISMATCH: There is a mismatch between the table and partition schemas
```

**Causa:** Schema da tabela diferente dos dados.

**Solucao:**
```sql
-- Verificar schema
DESCRIBE elo_fraud_dev_db.inference_logs;

-- Para inference_logs com Partition Projection, nao precisa de MSCK REPAIR
-- O schema e definido no Terraform
```

### Erro: Query Cancelled (Bytes Limit)

**Sintoma:**
```
Query cancelled: Bytes scanned limit was exceeded
```

**Solucao:**
```sql
-- Adicionar filtros de particao
SELECT * FROM inference_logs
WHERE year = 2024 AND month = 1 AND day = 15
LIMIT 1000;

-- Ou aumentar limite no Terraform
bytes_scanned_limit = 107374182400  # 100 GB
```

### Erro: Table Not Found

**Sintoma:**
```
Table not found: 'elo_fraud_dev_db'.'transaction_results'
```

**Solucao:**
```bash
# Verificar se database existe
aws glue get-database --name elo_fraud_dev_db

# Verificar se tabela existe
aws glue get-table --database-name elo_fraud_dev_db --name transaction_results
```

### Dados Nao Aparecem (inference_logs)

**Sintoma:** Query retorna 0 linhas mas dados existem no S3.

**Verificar:**
```bash
# Confirmar estrutura de pastas no S3
aws s3 ls s3://bucket/inference_logs/year=2024/month=01/day=15/hour=10/

# Deve ter arquivos .json
# Formato DEVE ser year=YYYY/month=MM/day=DD/hour=HH/
```

**Causa comum:** Firehose configurado com formato diferente de particao.

### Verificar Workgroup

```bash
# Status do workgroup
aws athena get-work-group \
  --work-group elo-fraud-athena-workgroup-dev

# Listar queries recentes
aws athena list-query-executions \
  --work-group elo-fraud-athena-workgroup-dev \
  --max-results 10
```

---

## Metricas CloudWatch

O workgroup publica metricas automaticamente:

| Metrica | Descricao |
|---------|-----------|
| `ProcessedBytes` | Bytes escaneados por query |
| `TotalExecutionTime` | Tempo total de execucao |
| `QueryQueueTime` | Tempo na fila |
| `QueryPlanningTime` | Tempo de planejamento |
| `EngineExecutionTime` | Tempo de execucao no engine |

### Alarme Sugerido

```hcl
resource "aws_cloudwatch_metric_alarm" "athena_bytes" {
  alarm_name          = "athena-high-bytes-scanned"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ProcessedBytes"
  namespace           = "AWS/Athena"
  period              = 3600
  statistic           = "Sum"
  threshold           = 50000000000  # 50 GB/hora

  dimensions = {
    WorkGroup = "elo-fraud-athena-workgroup-dev"
  }
}
```

---

## Operacoes

### Gerenciar Queries

```bash
# Executar query
aws athena start-query-execution \
  --query-string "SELECT * FROM inference_logs LIMIT 10" \
  --work-group "elo-fraud-athena-workgroup-dev" \
  --query-execution-context Database=elo_fraud_dev_db

# Ver status da query
aws athena get-query-execution \
  --query-execution-id "QUERY_ID"

# Listar queries recentes
aws athena list-query-executions \
  --work-group "elo-fraud-athena-workgroup-dev" \
  --max-results 10

# Ver resultados
aws athena get-query-results \
  --query-execution-id "QUERY_ID" \
  --output table
```

### Gerenciar Workgroup

```bash
# Ver configuracao do workgroup
aws athena get-work-group \
  --work-group "elo-fraud-athena-workgroup-dev"

# Atualizar limite de bytes
aws athena update-work-group \
  --work-group "elo-fraud-athena-workgroup-dev" \
  --configuration-updates BytesScannedCutoffPerQuery=20000000000

# Listar workgroups
aws athena list-work-groups \
  --output table
```

### Gerenciar Tabelas

```bash
# Listar tabelas no database
aws athena start-query-execution \
  --query-string "SHOW TABLES IN elo_fraud_dev_db" \
  --work-group "elo-fraud-athena-workgroup-dev"

# Ver schema da tabela
aws athena start-query-execution \
  --query-string "DESCRIBE elo_fraud_dev_db.inference_logs" \
  --work-group "elo-fraud-athena-workgroup-dev"

# Reparar particoes (se nao usar partition projection)
aws athena start-query-execution \
  --query-string "MSCK REPAIR TABLE elo_fraud_dev_db.inference_logs" \
  --work-group "elo-fraud-athena-workgroup-dev"
```

### Metricas e Monitoramento

```bash
# Bytes escaneados por hora
aws cloudwatch get-metric-statistics \
  --namespace AWS/Athena \
  --metric-name ProcessedBytes \
  --dimensions Name=WorkGroup,Value=elo-fraud-athena-workgroup-dev \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Sum

# Tempo de execucao
aws cloudwatch get-metric-statistics \
  --namespace AWS/Athena \
  --metric-name TotalExecutionTime \
  --dimensions Name=WorkGroup,Value=elo-fraud-athena-workgroup-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average
```

---

## Custos Estimados

### Precos Athena (sa-east-1)

| Componente | Preco | Nota |
|------------|-------|------|
| **Dados escaneados** | $5.00 / TB | Por query |
| **Minimo por query** | 10 MB | Mesmo para queries pequenas |

### Estimativa Mensal por Ambiente

| Ambiente | Queries/Dia | Dados/Query | Custo Estimado |
|----------|-------------|-------------|----------------|
| **DEV** | 20 | 100 MB | ~$3.00 |
| **STAGING** | 50 | 500 MB | ~$37.50 |
| **PROD** | 100 | 1 GB | ~$150.00 |

### Otimizacao de Custos

| Estrategia | Economia Potencial | Como Implementar |
|------------|-------------------|------------------|
| **Partition Projection** | ~50-80% | Evita MSCK REPAIR, queries mais rapidas |
| **Colunar (Parquet/ORC)** | ~80-90% | Escaneia apenas colunas necessarias |
| **Compressao (Snappy/ZSTD)** | ~50-70% | Menos dados para escanear |
| **Filtros de particao** | ~90%+ | WHERE year/month/day = X |
| **SELECT colunas especificas** | ~50-80% | Evitar SELECT * |
| **Limite de bytes (cutoff)** | Previne surpresas | bytes_scanned_cutoff |

### Comparativo: Query Otimizada vs Nao Otimizada

| Cenario | Dados Escaneados | Custo |
|---------|------------------|-------|
| SELECT * sem filtro (1 ano) | 500 GB | $2.50 |
| SELECT * com filtro (1 dia) | 1.5 GB | $0.0075 |
| SELECT colunas com filtro | 100 MB | $0.0005 |
| **Economia** | - | **99.98%** |

---

## Decisoes de Arquitetura

| Decisao | Justificativa |
|---------|---------------|
| **Partition Projection** | Elimina necessidade de MSCK REPAIR, particoes automaticas |
| **Formato Parquet** | Colunar, comprimido, eficiente para analytics |
| **Particao por year/month/day** | Padrao comum, otimiza queries por data |
| **Workgroup dedicado** | Isolamento de custos e configuracoes por ambiente |
| **Bytes cutoff 10 GB** | Previne queries acidentais que escaneiam tudo |
| **Resultado em S3 dedicado** | Facilita auditoria e limpeza de resultados |
| **Criptografia SSE-S3** | Padrao AWS, sem custo adicional |

---

## Referencias

### AWS Documentation

- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/latest/ug/)
- [Partition Projection](https://docs.aws.amazon.com/athena/latest/ug/partition-projection.html)
- [Athena Performance Tuning](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [Athena Pricing](https://aws.amazon.com/athena/pricing/)

### Terraform Documentation

- [aws_athena_workgroup](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/athena_workgroup)
- [aws_athena_database](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/athena_database)
- [aws_glue_catalog_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/glue_catalog_table)

### Best Practices

- [Athena Best Practices](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [Cost Optimization](https://aws.amazon.com/blogs/big-data/top-10-performance-tuning-tips-for-amazon-athena/)

