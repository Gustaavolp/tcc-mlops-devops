# Assumptions & Riscos – Fraud Scoring

>**Versão**: 1.0
**Data**: 2025-10-09
**Status**: Parcial

## 1) Assumptions atuais
- `purchaseDate` vem no formato `YYYYMMDDHHMMSS` e representa UTC; será convertido para `event_ts` (ISO UTC).
- `device_channel` será normalizado para `UPPER()`; domínio esperado `{BROWSER, SDK}` (ou `{01,02}` a confirmar).
- `purchase_currency` usa ISO numérico (`986 = BRL`); manter ambos (numérico/alfabético) se necessário.
- `browser_ip` pode não estar presente em transações `SDK`.
- PII (PAN, email, telefone) **não será persistida** em claro; apenas derivados (`bin`, `last4`) e `email_hash`.
- `nrid` será a **chave de correlação** entre 3DS e TE40 na SOT (a confirmar presença/formato).

## 2) Regras de validação e defaults (request)
- Campos obrigatórios ausentes → **rejeitar** (HTTP 400).
- Campos opcionais ausentes → imputar default e registrar em `warnings[]`.
- Normalizações:
  - `UPPER()` para `device_channel`, `mcc`, `merchant_country_code`.
  - Regex específicas:
    - `addr_match`: `[YN]`
    - `three_ds_eci`: `^[0-9]{2}$`
    - `three_ds_trans_status_reason`: `^\d{2}$`
    - `purchase_exponent`: `^\d{1}$`
- `browser_color_depth` deve ser curto (ex.: `"24"`).

## 3) Response e Telemetria
- `model_version` segue semver: `^v\d+\.\d+\.\d+$` (ex.: `v1.0.0`).
- Em fallback, **não** alterar `model_version` para sufixos; indicar em `error.fallback_applied: true`.
- Telemetria incluirá: `trace_id`, `timestamp`, `latency_ms`, `environment`, `status` (`success|fallback|error`).

## 4) Riscos / Pontos de atenção
- **`nrid`**: ausência no 3DS pode dificultar o join com TE40 → depender de mapeamento alternativo.
- **Late labels**: TE40 pode chegar dias depois → prever upsert/versão do label na SOT.
- Divergências de timezone → padronizar tudo em UTC no `event_ts`.
- Campos com regex rígida podem quebrar ingestão se a Elo variar formato → deixar validações claras e logs úteis.

## 5) Próximos passos (quando amostras chegarem)
- Validar schemas com **payload real** 3DS e TE40.
- Completar seção de campos TE40 e definição do label `is_fraud`.
- Fechar dicionário completo (v0.2) e publicar.

