# Dicionário de Dados – Fraud Scoring

**Versão**: 1.0
**Data**: 2025-10-09
**Status**: Parcial


## 1) Visão geral
Este dicionário descreve os campos que compõem o fluxo de detecção de fraude. Nesta versão, focamos no **pré-transacional (3DS)**; os campos **pós-transacionais (TE40)** serão adicionados quando a Elo enviar as amostras oficiais.

## 2) Convenções de nomenclatura
- Timestamps: `*_ts` (UTC ISO 8601), ex.: `event_ts`.
- Identificadores: `*_id`, ex.: `transaction_id`, `nrid`.
- Flags booleanas: `*_flag`, ex.: `fallback_applied_flag`.
- Códigos padronizados em `UPPER()` (ex.: `device_channel`, `mcc`, `merchant_country_code`).

## 3) Chaves e relacionamento
- `transaction_id`: identificador da autenticação 3DS (mapeado de `threeDSServerTransID`).
- `nrid` (**pendente Elo**): chave de correlação entre 3DS e TE40 (join para SOT).

## 4) Campos do 3DS (confirmados nesta fase)

| Campo canônico | Origem (3DS) | Tipo | Obrigatório | Regra/Validação | Observações |
|---|---|---:|:--:|---|---|
| `transaction_id` | `threeDSServerTransID` | string | ✅ | 6–64 chars | ID único do evento 3DS |
| `card_number` | `acctNumber` | string | ✅ | 13–19 dígitos | **Não persistir PAN**; derivar `bin`, `last4` |
| `bin` | derivado | string | — | primeiros 6 dígitos | PII-safe |
| `last4` | derivado | string | — | últimos 4 dígitos | PII-safe |
| `purchase_amount` | `purchaseAmount` | string/number | ✅ | >0 | converter para `amount_cents` |
| `amount_cents` | derivado | int | — | `int(round(amount*100))` | centavos |
| `purchase_currency` | `purchaseCurrency` | string | ✅ | ISO (ex.: `986`) | normalizar |
| `event_ts` | `purchaseDate` | timestamp | ✅ | `YYYYMMDDHHMMSS` → UTC ISO | era `purchaseDate` |
| `device_channel` | `deviceChannel` | string | ⚠️ | `{BROWSER, SDK}` ou `{01,02}` | confirmar Elo |
| `mcc` | `mcc` | string | — | regex `[0-9]{4}` | categoria do comércio |
| `merchant_country_code` | `merchantCountryCode` | string | — | ISO-3166 num (ex.: `076`) | `UPPER()` |
| `browser_ip` | `browserIP` | string | — | IPv4/IPv6 válido | derivar `geo_country` |
| `three_ds_trans_status` | `threeDSTransStatus` | string | — | enum `{Y,N,A,U,R}` | status 3DS |
| `three_ds_eci` | `threeDSEci` | string | — | regex `^[0-9]{2}$` | ECI |
| `addr_match` | `addrMatch` | string | — | regex `[YN]` | **exemplo de regra** |
| `browser_color_depth` | `browserColorDepth` | string | — | ex.: `"24"` | curta |
| `purchase_exponent` | `purchaseExponent` | string | — | `\d{1}` | ex.: `"2"` |
| `purchase_instal_data` | `purchaseInstalData` | string | — | limite de tamanho | ex.: `"0"` |
| `three_ds_trans_status_reason` | `threeDSTransStatusReason` | string | — | `\d{2}` | ex.: `"01"` |
| `email_hash` | `email` | string | — | hash/mascarar | não persistir email puro |

> Obs.: manter uma coluna `warnings` (array) para registrar imputações/defaults aplicados na normalização.

## 5) Campos esperados do TE40 (pendente Elo)

| Campo canônico | Origem (TE40) | Tipo | Obrigatório | Observações |
|---|---|---|:--:|---|
| `nrid` | (a confirmar) | string | ✅ | chave de correlação 3DS↔TE40 |
| `transaction_status` | (a confirmar) | string | — | status final |
| `chargeback_flag` | (a confirmar) | int(0/1) | — | base p/ `is_fraud` |
| `decision_ts` | (a confirmar) | timestamp | — | quando o status consolidou |
| `is_fraud` | derivado (TE40) | int(0/1) | — | mapeamento dos códigos TE40 |

## 6) Features derivadas (para SPEC, quando aplicável)

| Feature | Base | Regra | Tipo | Utilidade |
|---|---|---|---|---|
| `hour_of_day` | `event_ts` | `UTC.hour` | int [0–23] | padrão horário |
| `weekday` | `event_ts` | `isoweekday()` | int [1–7] | sazonalidade |
| `device_channel_is_sdk` | `device_channel` | `== 'SDK'` | bool | comportamento |
| `geo_country` | `browser_ip` | geolookup | string | risco por origem |

## 7) Qualidade e máscaras (PII)
- **PAN/email/telefone:** não persistir bruto; derivar/mascarar/hash.
- `UPPER()` para valores categóricos.
- Datas sempre em **UTC ISO**.
- `warnings[]` para defaults imputados.
- Rejeitar request quando faltar **obrigatórios** (HTTP 400).

## 8) Dependências externas (a confirmar com Elo)
- Presença/forma do **`nrid`** no 3DS/TE40 (chave de join).
- Domínio final de **`device_channel`**.
- Padrões definitivos de **campos com regex** (ex.: `three_ds_trans_status_reason`).
- Mapeamento TE40 → `is_fraud`.

## 9) Versionamento
- v0.1 — campos 3DS confirmados; TE40 pendente.


