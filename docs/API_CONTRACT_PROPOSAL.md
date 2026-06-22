# Proposta de Contrato de API - Scoring de Fraude

**Versão**: 1.0
**Data**: 2025-10-02
**Status**: Proposta para validação com cliente

---

## Visão Geral

Este documento apresenta a proposta de contrato de API para o serviço de **Scoring de Fraude em Tempo Real** da Elo. O serviço receberá dados completos do fluxo 3DS e retornará um score de fraude com recomendação de ação.

---

## Fluxo de Integração

```
Cliente → 3DS Service → OnlinePurchaseRequest + UnifiedResponse
                              ↓
Cliente → Nossa API de Fraude → Recebe dados mapeados
                              ↓
Nossa API → Processa com ML → Retorna FraudScoringResponse
```

---

## 1. Endpoint Proposto

### `POST /v1/score`

**Descrição**: Avalia o risco de fraude de uma transação online.

**Headers**:
```http
Content-Type: application/json
X-Trace-Id: <uuid>  (opcional - para rastreamento)
X-Client-Version: <version>  (opcional)
```

**SLA**:
- p50 ≤ 150ms
- p95 ≤ 500ms
- p99 ≤ 800ms
- Disponibilidade: ≥ 99.9%

---

## 2. Request Schema

### Mapeamento de Campos

Nossa API recebe campos mapeados do fluxo 3DS do cliente:

| Campo Nossa API | Origem no OpenAPI do Cliente | Tipo | Obrigatório |
|----------------|------------------------------|------|-------------|
| `transaction_id` | `threeDSServerTransID` | string(36) | ✅ Sim |
| `card_number` | `acctNumber` | string(13-19) | ✅ Sim |
| `purchase_amount` | `purchaseAmount` | string | ✅ Sim |
| `purchase_currency` | `purchaseCurrency` | string(3) | ✅ Sim |
| `purchase_date` | `purchaseDate` | string(14) | ✅ Sim |
| `device_channel` | `deviceChannel` | enum | ✅ Sim |
| `mcc` | `mcc` | string(4) | Não |
| `merchant_country_code` | `merchantCountryCode` | string(3) | Não |
| `cardholder_document` | `cardHolderDocument` | string(11) | Não |
| `email` | `email` | email | Não |
| `browser_ip` | `browserIP` | string | Não |
| `acct_info.*` | `acctInfo.*` | object | Não |
| `payment_info.*` | `paymentInfo.*` | object | Não |
| `merchant_risk_indicator.*` | `merchantRiskIndicator.*` | object | Não |
| `three_ds_trans_status` | `transStatus` (UnifiedResponse) | enum | Não |
| `three_ds_eci` | `eci` (UnifiedResponse) | string | Não |
| ... | ... | ... | ... |

**Total**: ~40 campos mapeados (6 obrigatórios, demais opcionais)

### Exemplo de Request

```json
{
  "transaction_id": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
  "card_number": "4111111111111111",
  "purchase_amount": "12345",
  "purchase_currency": "986",
  "purchase_exponent": "2",
  "purchase_date": "20231215120000",
  "device_channel": "02",
  "mcc": "5411",
  "merchant_country_code": "076",
  "merchant_document": "12345678000112",
  "cardholder_document": "12345678910",
  "email": "cliente@example.com",
  "mobile_phone": {
    "cc": "55",
    "subscriber": "11987654321"
  },
  "billing_address": {
    "city": "São Paulo",
    "state": "SP",
    "postal_code": "01310-100",
    "country": "076"
  },
  "shipping_address": {
    "city": "São Paulo",
    "state": "SP",
    "postal_code": "01310-100",
    "country": "076"
  },
  "addr_match": "Y",
  "browser_ip": "192.168.1.1",
  "browser_language": "pt-BR",
  "device_info": {
    "operating_system": "iOS",
    "version": "16.7",
    "name": "Safari",
    "latitude": "-23.550520",
    "longitude": "-46.633308"
  },
  "acct_info": {
    "txn_activity_day": "2",
    "txn_activity_year": "45",
    "suspicious_acc_activity": "02"
  },
  "payment_info": {
    "cof_number": 3,
    "cof_number_24h": 0,
    "cof_number_7d": 1
  },
  "three_ds_trans_status": "Y",
  "three_ds_eci": "05",
  "is_quick_withdrawal": false
}
```

---

## 3. Response Schema

### Campos da Resposta

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `transaction_id` | string(36) | ✅ Sim | ID da transação processada |
| `score` | number | ✅ Sim | Score de fraude (0.0 a 1.0) |
| `risk_band` | enum | ✅ Sim | LOW, MEDIUM, HIGH, CRITICAL |
| `recommendation` | enum | ✅ Sim | APPROVE, REVIEW, DECLINE, CHALLENGE |
| `reason_codes` | array | ✅ Sim | Top-5 features explicativas |
| `model_version` | string | ✅ Sim | Versão do modelo (ex: v1.0.0) |
| `timestamp` | datetime | ✅ Sim | Timestamp ISO 8601 |
| `latency_ms` | integer | ✅ Sim | Latência em milissegundos |
| `trace_id` | string | ✅ Sim | UUID para rastreamento |
| `model_metadata` | object | Não | Metadados do modelo |
| `performance_metrics` | object | Não | Métricas de performance |
| `environment` | enum | Não | dev, stg, prd |
| `warnings` | array | Não | Avisos sobre a predição |
| `error` | object | Não | Informações de erro |

### Exemplo de Response (Sucesso)

```json
{
  "transaction_id": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
  "score": 0.73,
  "risk_band": "HIGH",
  "recommendation": "REVIEW",
  "reason_codes": [
    {
      "code": "RC01",
      "description": "Múltiplas transações em curto período (velocity)",
      "impact": 0.25
    },
    {
      "code": "RC02",
      "description": "Primeiro uso do cartão neste merchant",
      "impact": 0.18
    },
    {
      "code": "RC03",
      "description": "Valor da transação acima da média do cliente",
      "impact": 0.15
    },
    {
      "code": "RC04",
      "description": "Horário atípico para este cliente",
      "impact": 0.10
    },
    {
      "code": "RC05",
      "description": "Geolocalização inconsistente com histórico",
      "impact": 0.05
    }
  ],
  "model_version": "v1.0.0",
  "timestamp": "2023-12-15T12:00:00.123Z",
  "latency_ms": 245,
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_metadata": {
    "features_count": 42,
    "enriched_from_history": true,
    "history_transactions_found": 5
  },
  "performance_metrics": {
    "inference_time_ms": 120,
    "feature_engineering_time_ms": 80,
    "db_lookup_time_ms": 45
  },
  "environment": "prd"
}
```

### Exemplo de Response (Com Warnings)

```json
{
  "transaction_id": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
  "score": 0.42,
  "risk_band": "MEDIUM",
  "recommendation": "APPROVE",
  "reason_codes": [
    {
      "code": "RC10",
      "description": "Cliente com bom histórico de transações",
      "impact": -0.30
    }
  ],
  "model_version": "v1.0.0",
  "timestamp": "2023-12-15T12:00:01.456Z",
  "latency_ms": 189,
  "trace_id": "660e8400-e29b-41d4-a716-446655440111",
  "warnings": [
    {
      "code": "MISSING_FIELD",
      "message": "Campo 'acct_info.txn_activity_day' não fornecido, usando valor padrão 0"
    },
    {
      "code": "MISSING_HISTORY",
      "message": "Nenhuma transação encontrada no histórico recente"
    }
  ],
  "environment": "prd"
}
```

### Exemplo de Response (Erro com Fallback)

```json
{
  "transaction_id": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
  "score": 0.50,
  "risk_band": "MEDIUM",
  "recommendation": "REVIEW",
  "reason_codes": [],
  "model_version": "v0.0.1-fallback",
  "timestamp": "2023-12-15T12:00:02.789Z",
  "latency_ms": 550,
  "trace_id": "770e8400-e29b-41d4-a716-446655440222",
  "error": {
    "code": "MODEL_TIMEOUT",
    "message": "Timeout ao chamar SageMaker endpoint",
    "detail": "Endpoint 'elo-fraud-score-prd' não respondeu em 500ms",
    "fallback_applied": true
  },
  "environment": "prd"
}
```

---

## 4. Interpretação dos Campos

### Score (0.0 - 1.0)
- **0.0 - 0.3**: Baixo risco de fraude
- **0.3 - 0.6**: Risco moderado
- **0.6 - 0.8**: Alto risco
- **0.8 - 1.0**: Risco crítico

### Risk Band
- **LOW**: Transação de baixo risco, aprovação automática recomendada
- **MEDIUM**: Risco moderado, pode necessitar revisão
- **HIGH**: Alto risco, revisão manual recomendada
- **CRITICAL**: Risco crítico, bloqueio recomendado

### Recommendation
- **APPROVE**: Aprovar transação automaticamente
- **REVIEW**: Enviar para análise manual
- **DECLINE**: Negar transação
- **CHALLENGE**: Solicitar autenticação adicional (step-up)

### Reason Codes
Lista ordenada (do maior para o menor impacto) das features que mais contribuíram para o score:
- **code**: Identificador único do código de razão
- **description**: Explicação em linguagem natural
- **impact**: Valor SHAP ou similar (-1.0 a 1.0)
  - Positivo: aumentou o score (mais risco)
  - Negativo: diminuiu o score (menos risco)

---

## 5. Códigos de Erro HTTP

| Código | Descrição | Quando Ocorre |
|--------|-----------|---------------|
| `200 OK` | Sucesso | Score calculado com sucesso |
| `400 Bad Request` | Erro de validação | Campos obrigatórios faltando ou formato inválido |
| `422 Unprocessable Entity` | Erro de negócio | Dados válidos mas não processáveis (ex: cartão inválido) |
| `500 Internal Server Error` | Erro interno | Falha no modelo ou infraestrutura |
| `503 Service Unavailable` | Serviço indisponível | Endpoint em manutenção ou sobrecarga |
| `504 Gateway Timeout` | Timeout | Resposta não retornada dentro do SLA |

### Exemplo de Erro 400 (Bad Request)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Campos obrigatórios faltando",
    "detail": "Os seguintes campos são obrigatórios: transaction_id, card_number, purchase_amount, purchase_currency, purchase_date, device_channel",
    "fields": [
      {
        "field": "card_number",
        "error": "Campo obrigatório não fornecido"
      },
      {
        "field": "purchase_amount",
        "error": "Campo obrigatório não fornecido"
      }
    ]
  },
  "trace_id": "880e8400-e29b-41d4-a716-446655440333",
  "timestamp": "2023-12-15T12:00:03.000Z"
}
```

---

## 6. Campos Opcionais e Estratégia de Fallback

### Campos Obrigatórios (Mínimo para Scoring)
Estes 6 campos são **obrigatórios** e sem eles a API retornará erro 400:
1. `transaction_id`
2. `card_number`
3. `purchase_amount`
4. `purchase_currency`
5. `purchase_date`
6. `device_channel`

### Campos Opcionais (Melhoram a Acurácia)
Todos os demais ~34 campos são **opcionais**, mas **altamente recomendados**:
- **Quanto mais campos enviados, maior a acurácia do modelo**
- Campos faltantes serão tratados com:
  - Valores padrão (ex: 0 para contadores)
  - Features derivadas (ex: BIN do cartão)
  - Imputação baseada em histórico

### Aviso de Qualidade
Se muitos campos opcionais estiverem faltando, incluiremos `warnings` na resposta indicando:
- Quais campos estão faltando
- Potencial impacto na acurácia
- Recomendação de enviar mais dados

---

## 7. Segurança e Compliance

### Dados Sensíveis
- **PCI-DSS**: O campo `card_number` deve ser enviado de forma segura
- **LGPD**: Dados pessoais (CPF, email, telefone) serão processados conforme LGPD
- **Encriptação**: Todas as comunicações via HTTPS/TLS 1.3

### Retenção de Dados
- **Logs de transação**: 90 dias (para auditoria)
- **Dados pessoais**: Anonimizados após 30 dias
- **Modelos**: Versionados e auditáveis

### Rastreabilidade
- Cada requisição recebe um `trace_id` único
- Logs estruturados com rastreamento end-to-end
- Auditoria completa de decisões do modelo

---

## 8. Testes e Homologação

### Ambiente de Testes
- **URL**: `https://fraud-api-dev.elo.com/v1/score`
- **Autenticação**: API Key (será fornecida)
- **Rate Limit**: 100 req/min (dev), 1000 req/min (prd)

### Casos de Teste Sugeridos

#### Teste 1: Transação Legítima
```json
{
  "transaction_id": "test-001-legitimate",
  "card_number": "4111111111111111",
  "purchase_amount": "10000",
  "purchase_currency": "986",
  "purchase_date": "20231215120000",
  "device_channel": "02"
}
```
**Resultado Esperado**: `score < 0.3`, `risk_band = LOW`, `recommendation = APPROVE`

#### Teste 2: Transação Suspeita (Velocity)
```json
{
  "transaction_id": "test-002-velocity",
  "card_number": "4111111111111111",
  "purchase_amount": "50000",
  "purchase_currency": "986",
  "purchase_date": "20231215120100",
  "device_channel": "02",
  "acct_info": {
    "txn_activity_day": "10"
  }
}
```
**Resultado Esperado**: `score > 0.6`, `risk_band = HIGH`, `recommendation = REVIEW`

#### Teste 3: Campos Obrigatórios Faltando
```json
{
  "transaction_id": "test-003-missing-fields"
}
```
**Resultado Esperado**: HTTP 400, erro de validação

---

## 9. Versionamento da API

### Política de Versionamento
- **Major**: Mudanças breaking (ex: campos obrigatórios novos)
- **Minor**: Novos campos opcionais ou features
- **Patch**: Bug fixes e otimizações

### Versão Atual Proposta
- **v1.0.0** (esta proposta)

### Compatibilidade
- Manteremos a versão anterior por **6 meses** após lançamento de nova major version
- Clientes serão notificados com **3 meses** de antecedência sobre deprecações

---

## 10. Próximos Passos

### Para Aprovação desta Proposta

1. **Revisão dos Schemas** (você está aqui)
   - [ ] Validar campos obrigatórios
   - [ ] Validar campos opcionais
   - [ ] Validar estrutura da resposta
   - [ ] Validar códigos de erro

2. **Validação de Negócio**
   - [ ] Aprovar risk_bands e recommendations
   - [ ] Validar reason_codes e explicabilidade
   - [ ] Definir thresholds de score

3. **Acordo de SLA**
   - [ ] Confirmar latências (p50, p95, p99)
   - [ ] Confirmar disponibilidade (99.9%)
   - [ ] Definir políticas de fallback

4. **Segurança e Compliance**
   - [ ] Validar tratamento de dados sensíveis
   - [ ] Aprovar políticas de retenção
   - [ ] Validar conformidade LGPD

5. **Implementação**
   - [ ] Desenvolvimento da API (Sprint 1-3)
   - [ ] Testes integrados (Sprint 3-4)
   - [ ] Go-Live (Sprint 4)

---

## 11. Contatos

**Tech Lead**: Cristovam
**Email**: [contato]
**Repositório**: [link do repo]
**Schemas**: `schemas/fraud_scoring_request.schema.json` e `schemas/fraud_scoring_response.schema.json`

---

## Anexos

### Referências
- [BUILD_STRATEGY.md](../BUILD_STRATEGY.md) - Estratégia de 60 dias
- [AI_AGENT_GUIDE.md](../AI_AGENT_GUIDE.md) - Referência rápida de arquitetura
- [schemas/fraud_scoring_request.schema.json](../schemas/fraud_scoring_request.schema.json) - Schema completo de request
- [schemas/fraud_scoring_response.schema.json](../schemas/fraud_scoring_response.schema.json) - Schema completo de response

### Mapeamento Completo OpenAPI → Nossa API
Ver arquivo: `schemas/fraud_scoring_request.schema.json` para mapeamento detalhado de todos os ~40 campos.

---

**Última atualização**: 2025-10-02
**Status**: 🟡 Aguardando aprovação do cliente
