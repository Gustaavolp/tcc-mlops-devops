#  Definição inicial do Dataset (campos, origem, qualidade)  

## 1️- Visão Geral

Este documento define os campos que compõem o **dataset base** para o modelo de detecção de fraudes.  
Atualmente, o escopo cobre **dados pré-transacionais (3DS)** e prevê integração futura com **dados pós-transacionais (TE40)**, que ainda estão pendentes de envio pela Elo.

O objetivo é estabelecer:
- O **contrato de dados** entre as origens e o pipeline;
- As **regras de preenchimento e padronização**;
- As **features derivadas** que serão usadas para modelagem.

---

## 2️- Fontes e Chaves

| Tipo | Descrição | Status | Observações |
|------|------------|---------|-------------|
| **3DS (pré-transacional)** | Dados de autenticação 3D Secure enviados pela Elo via API | Payload de exemplo | Usado para features de comportamento de compra |
| **TE40 (pós-transacional)** | Dados de confirmação e chargeback (labels de fraude) |  Pendente Elo | Será usado para geração do label `is_fraud` |
| **NRID** | Identificador único da transação |  A confirmar formato | Será usado para join 3DS ↔ TE40 |
| **transaction_id** | Identificador interno do 3DS |  Confirmado | Mapeado de `threeDSServerTransID` |

---

## 3- Campos do 3DS (esperados)
**(pendente Elo)**

| Campo original | Campo canônico | Tipo | Obrigatório | Regra / Transformação | Observações |
|----------------|----------------|------|--------------|------------------------|--------------|
| `threeDSServerTransID` | `transaction_id` | string | ✅ | manter | Identificador único do evento 3DS |
| `acctNumber` | `card_number` | string | ✅ | mascarar → derivar `bin`, `last4` | não persistir PAN completo |
| `purchaseAmount` | `purchase_amount` | number | ✅ | converter para `amount_cents` (int) | unidade: centavos |
| `purchaseCurrency` | `purchase_currency` | string | ✅ | normalizar (ISO numérico ou alfabético) | ex: 986 ou BRL |
| `purchaseDate` | `event_ts` | string → timestamp | ✅ | converter formato `YYYYMMDDHHMMSS` → UTC ISO | timezone a confirmar |
| `deviceChannel` | `device_channel` | string | ⚠️ | `upper()` | domínio BROWSER/SDK (ou 01/02?) |
| `merchantCountryCode` | `merchant_country_code` | string | ⚙️ | `upper()` | ISO-3166 |
| `mcc` | `mcc` | string | ⚙️ | regex `[0-9]{4}` | categoria do comércio |
| `browserIP` | `browser_ip` | string | opcional | validar IPv4/6 | derivar país (geo lookup) |
| `threeDSEci` | `three_ds_eci` | string | opcional | manter | código de autenticação |
| `threeDSTransStatus` | `three_ds_trans_status` | string | opcional | manter | status Y/N/A/U/R |
| `email` | `email_hash` | string | opcional | hash domínio + local | anonimizar |
| `mobilePhone` | `mobile_phone_cc` / `mobile_phone_num` | objeto → string | opcional | normalizar `+55` / remover símbolos | — |

---

## 4️- Features derivadas (engenharia de dados)

| Feature | Base | Regra | Tipo | Observações |
|----------|------|-------|------|-------------|
| `amount_cents` | `purchaseAmount` | `int(round(valor * 100))` | int | unidade: centavos |
| `bin` | `acctNumber` | primeiros 6 dígitos | string | não sensível |
| `last4` | `acctNumber` | últimos 4 dígitos | string | não sensível |
| `hour_of_day` | `event_ts` | extrair hora UTC | int | faixa [0–23] |
| `weekday` | `event_ts` | `isoweekday()` | int | 1 = segunda |
| `device_channel_is_sdk` | `device_channel` | `== 'SDK'` | bool | — |
| `geo_country` | `browser_ip` | geo lookup | string | fallback `unknown` |

---

## 5️- Campos esperados do TE40 (pendente Elo)

| Campo | Tipo | Status | Descrição / Uso esperado |
|--------|------|---------|---------------------------|
| `nrid` | string | ⚠️ pendente | chave de join com 3DS |
| `transaction_status` | string | ⚠️ pendente | status final da transação |
| `chargeback_flag` | int(0/1) | ⚠️ pendente | label de fraude |
| `decision_date` | timestamp | ⚠️ pendente | data de confirmação |
| `merchant_id` | string | ⚠️ pendente | identificação do estabelecimento |
| `auth_result_code` | string | ⚠️ pendente | mapa de fraude / aprovação |

---

## 6️- Campos com dependência externa (a confirmar com Elo)

- Formato de `purchaseDate` (UTC ou GMT-3?)  
- Domínio de `deviceChannel` (BROWSER/SDK ou 01/02?)  
- Confirmação do campo `NRID` (nome e tipo idêntico no TE40 e 3DS?)  
- Regra de derivação do label (`is_fraud`) a partir do TE40 (chargeback ou outros códigos)  
- Formato da moeda (`purchaseCurrency`) — numérico ou textual 
- Confirmar se o campo `NRID` (Network Reference ID) está presente no payload 3DS.
- Caso não esteja, será necessário que a Elo informe um mecanismo de correlação entre 3DS e TE40 (ex: via transaction_id ou tabela de referência).


---

## 7️- Regras de qualidade e validação

| Tipo de validação | Descrição | Ação |
|--------------------|------------|------|
| Campos obrigatórios nulos | transaction_id, purchase_amount, purchase_date | Rejeitar payload (HTTP 400) |
| Campos opcionais ausentes | email, browser_ip, device_channel | imputar default e registrar em `warnings[]` |
| Normalização de strings | converter para `upper()` | aplicar antes de persistir |
| Campos PII | PAN, email, telefone | anonimizar ou truncar |
| Timestamps | devem estar em UTC ISO | converter e validar formato |

---

## 8️- Exemplos de payload

 Aguardando Elo 

---

## 9️- Versão e histórico

| Versão | Data | Autor | Observações |
|---------|------|--------|-------------|
| v0.1 | 2025-10-09 | Bruna Oliveira | Versão inicial com base no payload de exemplo do 3DS |


---
