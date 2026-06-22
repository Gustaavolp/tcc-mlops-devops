# Referencia de Payloads e Fluxos - Elo Fraud Detection

> **Documento Tecnico para Reuniao E2E**
> **Data**: 2026-01-16
> **Ambiente**: DEV (us-east-1)

---

## 1. Endpoint de Scoring

### 1.1 Informacoes do Endpoint

```
Metodo: POST
URL (ALB):     http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score
URL (API GW): https://oc9dm394cf.execute-api.us-east-1.amazonaws.com/v1/score
Content-Type: application/json
```

### 1.2 Estrutura do Request

```json
{
  // === CAMPOS OBRIGATORIOS ===
  "transaction_id": "string",        // ID unico da transacao
  "cardHolderDocument": "string",    // CPF/CNPJ do portador (chave de particionamento)
  "amount": "string",                // Valor da transacao (ex: "150.00")
  "cd_merchant_category_code": "string", // MCC do estabelecimento
  "cd_merchant_country": "string",   // Codigo do pais do merchant (ISO 3166)

  // === CAMPOS RECOMENDADOS ===
  "nm_merchant_country_name": "string",  // Nome do pais
  "cd_device_channel": "string",         // Canal: "01"=App, "02"=Browser, "03"=3RI
  "cd_browser_time_zone": "string",      // Timezone em minutos (ex: "-180")
  "nm_browser_language": "string",       // Idioma (ex: "pt-BR")
  "enr_device_os": "string",             // Sistema operacional
  "nm_cardholder_bill_addr_state": "string",   // Estado de cobranca
  "nm_cardholder_bill_addr_country": "string", // Pais de cobranca
  "nm_protocol": "string",               // Versao do protocolo 3DS
  "cd_transaction_status": "string",     // Status 3DS: Y/N/A/U/R/C
  "cd_eci": "string"                     // ECI: 01/02/05/06/07
}
```

### 1.3 Estrutura da Resposta

```json
{
  "transaction_id": "string",   // ID da transacao (echo)
  "score": 0.0,                 // Score de fraude (0.0 a 1.0)
  "fraud_label": 0              // Label: 0=legitima, 1=fraude
}
```

### 1.4 Regra de Classificacao

```
if score > 0.5:
    fraud_label = 1  (fraude)
else:
    fraud_label = 0  (legitima)
```

---

## 2. Exemplos de Payloads

### 2.1 Payload Minimo (Campos Obrigatorios)

```json
{
  "transaction_id": "MIN-001",
  "cardHolderDocument": "12345678901",
  "amount": "100.00",
  "cd_merchant_category_code": "5411",
  "cd_merchant_country": "BRA"
}
```

**Curl:**
```bash
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "MIN-001",
    "cardHolderDocument": "12345678901",
    "amount": "100.00",
    "cd_merchant_category_code": "5411",
    "cd_merchant_country": "BRA"
  }'
```

### 2.2 Payload Completo (Transacao Nacional)

```json
{
  "transaction_id": "FULL-BR-001",
  "cardHolderDocument": "12345678901",
  "amount": "299.90",
  "cd_merchant_category_code": "5411",
  "cd_merchant_country": "BRA",
  "nm_merchant_country_name": "Brazil",
  "cd_device_channel": "02",
  "cd_browser_time_zone": "-180",
  "nm_browser_language": "pt-BR",
  "enr_device_os": "Android",
  "nm_cardholder_bill_addr_state": "SP",
  "nm_cardholder_bill_addr_country": "BR",
  "nm_protocol": "2.2.0",
  "cd_transaction_status": "Y",
  "cd_eci": "05",
  "purchase_date": "20260116143000",
  "purchase_currency": "986",
  "purchase_exponent": "2",
  "browser_javascript_enabled": "true",
  "browser_screen_width": "1920",
  "browser_screen_height": "1080",
  "browser_color_depth": "24"
}
```

**Curl:**
```bash
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "FULL-BR-001",
    "cardHolderDocument": "12345678901",
    "amount": "299.90",
    "cd_merchant_category_code": "5411",
    "cd_merchant_country": "BRA",
    "nm_merchant_country_name": "Brazil",
    "cd_device_channel": "02",
    "cd_browser_time_zone": "-180",
    "nm_browser_language": "pt-BR",
    "enr_device_os": "Android",
    "nm_cardholder_bill_addr_state": "SP",
    "nm_cardholder_bill_addr_country": "BR",
    "nm_protocol": "2.2.0",
    "cd_transaction_status": "Y",
    "cd_eci": "05"
  }'
```

### 2.3 Payload Alto Valor (Potencial Fraude)

```json
{
  "transaction_id": "HIGH-VALUE-001",
  "cardHolderDocument": "98765432109",
  "amount": "15000.00",
  "cd_merchant_category_code": "5944",
  "cd_merchant_country": "USA",
  "nm_merchant_country_name": "United States",
  "cd_device_channel": "01",
  "cd_browser_time_zone": "-300",
  "nm_browser_language": "en-US",
  "enr_device_os": "iOS",
  "nm_cardholder_bill_addr_state": "NY",
  "nm_cardholder_bill_addr_country": "US",
  "nm_protocol": "2.2.0",
  "cd_transaction_status": "A",
  "cd_eci": "07"
}
```

### 2.4 Payload Internacional

```json
{
  "transaction_id": "INTL-001",
  "cardHolderDocument": "55544433322",
  "amount": "500.00",
  "cd_merchant_category_code": "5812",
  "cd_merchant_country": "PRT",
  "nm_merchant_country_name": "Portugal",
  "cd_device_channel": "02",
  "cd_browser_time_zone": "0",
  "nm_browser_language": "pt-PT",
  "enr_device_os": "Windows",
  "nm_cardholder_bill_addr_state": "Lisboa",
  "nm_cardholder_bill_addr_country": "PT",
  "nm_protocol": "2.1.0",
  "cd_transaction_status": "Y",
  "cd_eci": "05"
}
```

---

## 3. Campos do Payload - Dicionario

### 3.1 Identificacao

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `transaction_id` | string | Sim | ID unico da transacao | "TXN-123456" |
| `cardHolderDocument` | string | Sim | CPF/CNPJ do portador (11 ou 14 digitos) | "12345678901" |

### 3.2 Valor

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `amount` | string | Sim | Valor da transacao | "299.90" |
| `purchase_currency` | string | Nao | Codigo ISO 4217 da moeda | "986" (BRL) |
| `purchase_exponent` | string | Nao | Expoente decimal (default: 2) | "2" |

### 3.3 Merchant

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `cd_merchant_category_code` | string | Sim | MCC do estabelecimento | "5411" |
| `cd_merchant_country` | string | Sim | Codigo ISO do pais | "BRA" |
| `nm_merchant_country_name` | string | Nao | Nome do pais | "Brazil" |

### 3.4 Device/Browser

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `cd_device_channel` | string | Nao | Canal: 01=App, 02=Browser, 03=3RI | "02" |
| `cd_browser_time_zone` | string | Nao | Timezone em minutos | "-180" |
| `nm_browser_language` | string | Nao | Idioma do browser | "pt-BR" |
| `enr_device_os` | string | Nao | Sistema operacional | "Android" |
| `browser_javascript_enabled` | string | Nao | JavaScript habilitado | "true" |
| `browser_screen_width` | string | Nao | Largura da tela | "1920" |
| `browser_screen_height` | string | Nao | Altura da tela | "1080" |
| `browser_color_depth` | string | Nao | Profundidade de cor | "24" |

### 3.5 Endereco

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `nm_cardholder_bill_addr_state` | string | Nao | Estado de cobranca | "SP" |
| `nm_cardholder_bill_addr_country` | string | Nao | Pais de cobranca | "BR" |
| `nm_cardholder_ship_addr_state` | string | Nao | Estado de entrega | "RJ" |
| `nm_cardholder_ship_addr_country` | string | Nao | Pais de entrega | "BR" |

### 3.6 3DS (Autenticacao)

| Campo | Tipo | Obrigatorio | Descricao | Exemplo |
|-------|------|-------------|-----------|---------|
| `nm_protocol` | string | Nao | Versao do protocolo 3DS | "2.2.0" |
| `cd_transaction_status` | string | Nao | Status da autenticacao | "Y" |
| `cd_eci` | string | Nao | Electronic Commerce Indicator | "05" |

#### Valores de `cd_transaction_status`:
- `Y` - Autenticacao bem-sucedida
- `N` - Autenticacao falhou
- `A` - Tentativa de autenticacao
- `U` - Autenticacao indisponivel
- `R` - Autenticacao rejeitada
- `C` - Challenge exigido

#### Valores de `cd_eci`:
- `01` - Merchant liability (Mastercard)
- `02` - Issuer liability (Mastercard)
- `05` - Autenticado (Visa)
- `06` - Tentativa (Visa)
- `07` - Nao autenticado (Visa)

---

## 4. Medicao de Tempo de Resposta

### 4.1 Usando curl

```bash
# Metricas detalhadas
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TIME-001","cardHolderDocument":"12345678901","amount":"100.00","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}' \
  -w "\n\n=== METRICAS DE TEMPO ===
Tempo DNS:        %{time_namelookup}s
Tempo Conexao:    %{time_connect}s
Tempo SSL:        %{time_appconnect}s
Tempo Pre-Trans:  %{time_pretransfer}s
Tempo Redirect:   %{time_redirect}s
Tempo TTFB:       %{time_starttransfer}s
Tempo TOTAL:      %{time_total}s
\n"
```

### 4.2 Interpretacao das Metricas

| Metrica | Descricao | Target |
|---------|-----------|--------|
| `time_namelookup` | Resolucao DNS | < 10ms |
| `time_connect` | Conexao TCP | < 50ms |
| `time_starttransfer` | Time to First Byte (TTFB) | < 400ms |
| `time_total` | Tempo total da requisicao | < 500ms |

### 4.3 Script de Benchmark

```bash
#!/bin/bash
# benchmark.sh - Executa N requests e calcula estatisticas

URL="http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score"
PAYLOAD='{"transaction_id":"BENCH","cardHolderDocument":"11111111111","amount":"100.00","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}'
N=${1:-100}  # Numero de requests (default: 100)

echo "Executando $N requests..."
echo ""

# Arquivo temporario para resultados
RESULTS=$(mktemp)

for i in $(seq 1 $N); do
  curl -s -o /dev/null -w "%{time_total}\n" -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" >> "$RESULTS"
done

# Calcular estatisticas
echo "=== RESULTADOS ($N requests) ==="
echo ""

# Minimo, maximo, media
MIN=$(sort -n "$RESULTS" | head -1)
MAX=$(sort -n "$RESULTS" | tail -1)
AVG=$(awk '{sum+=$1} END {printf "%.4f", sum/NR}' "$RESULTS")

# p50, p95, p99
P50=$(sort -n "$RESULTS" | awk "NR==int($N*0.50)")
P95=$(sort -n "$RESULTS" | awk "NR==int($N*0.95)")
P99=$(sort -n "$RESULTS" | awk "NR==int($N*0.99)")

echo "Min:    ${MIN}s"
echo "Max:    ${MAX}s"
echo "Media:  ${AVG}s"
echo ""
echo "p50:    ${P50}s"
echo "p95:    ${P95}s"
echo "p99:    ${P99}s"
echo ""

# Verifica SLA
P95_MS=$(echo "$P95 * 1000" | bc)
echo "SLA (p95 < 500ms): $([ $(echo "$P95_MS < 500" | bc) -eq 1 ] && echo 'PASSOU' || echo 'FALHOU')"

rm "$RESULTS"
```

---

## 5. Fluxo de Dados Passo a Passo

### 5.1 Fluxo Sincrono Detalhado

```
CLIENTE                          SISTEMA
   |                                |
   |  1. POST /score               |
   |  (JSON payload)               |
   |------------------------------->|
   |                                |
   |                          2. API Gateway
   |                             - Valida JSON
   |                             - Rate limit check
   |                                |
   |                          3. ALB
   |                             - Health check OK
   |                             - Route to pod
   |                                |
   |                          4. Inference Pod
   |                             |
   |                             +-> 4a. Normalizar payload
   |                             |     - Converter tipos
   |                             |     - Validar campos
   |                             |
   |                             +-> 4b. Consultar DynamoDB
   |                             |     - Key: cardHolderDocument
   |                             |     - Ultimas 20 transacoes
   |                             |     - Calcular features historicas
   |                             |
   |                             +-> 4c. Feature Engineering
   |                             |     - 115+ features
   |                             |     - Rolling windows
   |                             |     - Lags (n-1, n-2, n-3)
   |                             |
   |                             +-> 4d. Model Inference
   |                             |     - XGBoost classifier
   |                             |     - predict_proba()
   |                             |
   |                             +-> 4e. Gerar Resposta
   |                             |     - Score (0.0-1.0)
   |                             |     - fraud_label (0 ou 1)
   |                             |
   |                             +-> 4f. Publicar SQS (async)
   |                                   - Nao bloqueia resposta
   |                                |
   |  5. JSON Response             |
   |<-------------------------------|
   |                                |
```

### 5.2 Fluxo Assincrono Detalhado

```
SQS FIFO                        PROCESS WORKER
   |                                |
   |  (mensagem na fila)            |
   |                                |
   |  1. Long Polling (20s)         |
   |<-------------------------------|
   |                                |
   |  2. Receber batch (max 10)     |
   |------------------------------->|
   |                                |
   |                          3. Para cada mensagem:
   |                             |
   |                             +-> 3a. Parse JSON
   |                             |
   |                             +-> 3b. Enviar Firehose
   |                             |     - Stream: transactions
   |                             |     - Stream: inference
   |                             |
   |                             +-> 3c. Salvar DynamoDB
   |                             |     - Update historico
   |                             |     - Manter ultimos 15
   |                             |
   |                             +-> 3d. Metricas CloudWatch
   |                                |
   |  4. Delete Message            |
   |<-------------------------------|
   |                                |

FIREHOSE                         S3
   |                                |
   |  5. Buffer (1MB ou 60s)        |
   |                                |
   |  6. Entregar batch             |
   |------------------------------->|
   |                                |
   |                          7. Salvar com particoes
   |                             landing_zone/
   |                               year=2026/
   |                                 month=01/
   |                                   day=16/
   |                                     hour=14/
   |                                       data.json
```

---

## 6. Tratamento de Erros

### 6.1 Codigos HTTP

| Codigo | Descricao | Acao |
|--------|-----------|------|
| 200 | Sucesso | Score retornado |
| 400 | Bad Request | Payload invalido |
| 500 | Internal Error | Erro no servidor |
| 502 | Bad Gateway | ALB nao conseguiu conectar |
| 503 | Service Unavailable | Modelo nao carregado |
| 504 | Gateway Timeout | Timeout na inferencia |

### 6.2 Exemplo de Erro

```json
// Request com campo faltante
POST /score
{
  "transaction_id": "ERR-001"
}

// Response (400)
{
  "detail": "Missing required field: cardHolderDocument"
}
```

### 6.3 Validacao de Payload

```bash
# Testar payload invalido
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}'
```

---

## 7. Headers Recomendados

```bash
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: $(uuidgen)" \
  -H "X-Correlation-ID: E2E-TEST-001" \
  -d @payload.json
```

---

## 8. Payloads para Testes Especificos

### 8.1 Teste de Idempotencia

```bash
# Enviar mesmo transaction_id 2x
PAYLOAD='{"transaction_id":"IDEMP-001","cardHolderDocument":"12345678901","amount":"100.00","cd_merchant_category_code":"5411","cd_merchant_country":"BRA"}'

curl -X POST http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" -d "$PAYLOAD"

curl -X POST http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" -d "$PAYLOAD"

# Ambos devem retornar o mesmo score
```

### 8.2 Teste de Carga Sequencial

```bash
# 50 transacoes sequenciais
for i in {1..50}; do
  curl -s -X POST \
    http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
    -H "Content-Type: application/json" \
    -d "{\"transaction_id\":\"LOAD-$i\",\"cardHolderDocument\":\"12345678901\",\"amount\":\"$((i*10)).00\",\"cd_merchant_category_code\":\"5411\",\"cd_merchant_country\":\"BRA\"}"
  echo ""
done
```

### 8.3 Teste de Usuario Novo (Sem Historico)

```bash
# Documento nunca visto antes
curl -X POST \
  http://elo-fraud-alb-dev-v2-1654693652.us-east-1.elb.amazonaws.com/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "NEW-USER-001",
    "cardHolderDocument": "99999999999",
    "amount": "150.00",
    "cd_merchant_category_code": "5411",
    "cd_merchant_country": "BRA"
  }'
```

---

*Documento gerado em 2026-01-15*
