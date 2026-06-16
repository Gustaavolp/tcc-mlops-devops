# Feature Spec — Fraud Scoring (Draft)

Este documento descreve um conjunto priorizado de features derivadas do contrato de request (`schemas/fraud_scoring_request.schema.json`). Inclui convenções, entidades/janelas, listas de features diretas, enriquecidas, agregadas e cruzadas, além de observações de privacidade e encoding.

## Convenções

- Prefixos: `f_` (direta), `enr_` (enriquecida), `agg_` (agregada), `x_` (cruzada), `q_` (qualidade).
- Tipos: numérica, categórica, binária. Encoding sugerido: one‑hot/WOE/frequência.
- Valor: `purchase_amount` deve ser convertido com `purchase_exponent` (default 2 se ausente) e pode ter `log1p`.
- Tempo: `purchase_date` é `YYYYMMDDHHMMSS` (UTC). Usar `browser_tz` (minutos) para hora local quando aplicável.
- Entidades/chaves: `card_hash` (PAN hash), `device_hash`, `email`, `phone`, `browser_ip` (/24), `acquirer_merchant_id`, `merchant_document`, `mcc`.
- Janelas: 1h, 24h, 7d, 30d, 90d; métricas de recência (`first_seen`, `last_seen`).

## Diretas do Request (Alta prioridade)

- f_amount_value — numérica | int(amount)×10^-exponent | valor normalizado.
- f_amount_log — numérica | log1p(f_amount_value) | estabiliza cauda longa.
- f_amount_bucket — categórica | binning por quantis/regra | captura não linearidade.
- f_installments_n — numérica | `purchase_instal_data`→int (default 1) | risco de longas parcelas.
- f_is_quick_withdrawal — binária | `is_quick_withdrawal` | saque é alto risco.
- f_weekend — binária | dia_semana in {6,7} | padrão temporal.
- f_hour_local — numérica | hora local por `browser_tz` | compras de madrugada.
- f_addr_match — binária | `addr_match` (Y/N) | divergência de endereço.
- f_bill_ship_country_match — binária | billing.country==shipping.country | divergência geográfica.
- f_nb_purchase_account — numérica | `acct_info.nb_purchase_account` | velocidade de compras.
- f_txn_activity_day — numérica | `acct_info.txn_activity_day` | spike de atividade.
- f_txn_activity_ratio — numérica | day/max(year,1) | normaliza velocidade.
- f_suspicious_acc_activity — binária | `acct_info.suspicious_acc_activity` | suspeita prévia.
- f_device_channel — categórica | `device_channel` | comportamento por canal.
- f_mcc — categórica | `mcc` | risco por setor.
- f_3ds_status — categórica | `three_ds_trans_status` | nível de autenticação.
- f_3ds_eci — categórica | `three_ds_eci` | força de autenticação.

## Diretas do Request (Média prioridade)

- f_currency_iso3 — categórica | `purchase_currency` | cross‑border.
- f_recurring_amount_ind — categórica | `recurring_ind.amount_ind` | recorrência.
- f_recurring_frequency_ind — categórica | `recurring_ind.frequency_ind` | frequência.
- f_js_enabled — binária | `browser_javascript_enabled` | automação/bot.
- f_java_enabled — binária | `browser_java_enabled` | fingerprint.
- f_browser_lang — categórica | `browser_language` | consistência geo.
- f_color_depth — numérica | `browser_color_depth`→int | fingerprint.
- f_screen_w/h — numéricas | `browser_screen_width/height`→int | fingerprint.
- f_tz_offset_min — numérica | `browser_tz`→int | consistência geo.
- f_user_agent_family — categórica | parse UA (família) | device/navegador.
- f_user_agent_os — categórica | parse UA (OS) | fingerprint.
- f_merchant_country_code — categórica | `merchant_country_code` | cross‑border.
- f_is_direct_selling — binária | `is_direct_selling` | modelo de venda.
- f_gift_card_amount_ratio — numérica | gift_card_amount/amount | abuso gift card.
- f_gift_card_count — numérica | `gift_card_count`→int | volume gift card.
- f_pre_order_ind — binária | `pre_order_purchase_ind` | risco diferenciado.
- f_cof_recency_days — numérica | now − `payment_info.cof_date` | recência do COF.

## Enriquecimento Externo (lookup/serviços)

- enr_card_bin6/enr_card_bin8 — categóricas | prefixo do PAN | chave para lookup.
- enr_card_luhn_valid — binária | Luhn | formato válido.
- enr_card_brand/type/product — categóricas | BIN lookup | risco por produto.
- enr_issuer_country — categórica | BIN lookup | país emissor.
- enr_ip_country/region/city — categóricas | GeoIP | localização.
- enr_ip_asn/autonomous_system — categóricas | GeoIP | ASN (datacenter).
- enr_ip_is_proxy_vpn — binária | listas de reputação | anonimato.
- enr_ip_distance_km_billing — numérica | GeoIP + geocode CEP | haversine.
- enr_email_domain — categórica | domínio do email | reputação.
- enr_email_is_disposable — binária | listas | domínio descartável.
- enr_phone_country — categórica | `mobile_phone.cc` | consistência geo.
- enr_lang_country — categórica | `browser_language`→país | consistência geo.

## Agregações (Feature Store)

- agg_card_txn_24h_count — card_hash,24h | count | velocidade cartão.
- agg_card_txn_7d_count — card_hash,7d | count | baseline curto.
- agg_card_ticket_30d_mean/std — card_hash,30d | média/desvio | ticket típico.
- agg_card_chargeback_rate_90d — card_hash,90d | cb/tx | risco histórico.
- agg_email_merchants_30d_nunique — email,30d | distintos merchants | dispersão.
- agg_device_cards_7d_nunique — device_hash,7d | distintos cartões | rotação.
- agg_ip_cards_24h_nunique — ip/24,24h | distintos cartões | enumeração.
- agg_merchant_devices_7d_nunique — merchant,7d | distintos devices | ataque ao merchant.
- agg_pair_card_email_days_since_first — par,all | dias desde 1ª | novidade do par.
- agg_pair_card_device_hours_since_first — par,all | horas desde 1ª | device novo.
- agg_geo_card_countries_30d_nunique — card_hash,30d | países | dispersão geo.

## Cruzadas e Consistência

- x_geo_ip_vs_billing_country_mismatch — enr_ip_country ≠ billing.country.
- x_geo_ip_vs_bin_country_mismatch — enr_ip_country ≠ enr_issuer_country.
- x_lang_vs_ip_country_mismatch — idioma browser ≠ enr_ip_country.
- x_channel_vs_js_inconsistent — device_channel=02 & !f_js_enabled.
- x_giftcard_high_ratio — f_gift_card_amount_ratio>0.5.
- x_high_value_long_installments — valor alto & parcelas altas.
- x_3ds_fail_high_value — 3DS∈{N,U,R} & valor alto.
- x_new_device_high_value — device “novo” & valor alto.

## Qualidade e Privacidade

- q_missing_exponent — faltante `purchase_exponent`.
- q_invalid_pan_format — regex falhou para PAN.
- q_invalid_email_format — formato inválido.
- q_postal_code_invalid_len — CEP inválido.
- q_user_agent_missing — UA ausente/curto.
- Privacidade: derivar apenas BIN6/8 e `card_hash`; nunca persistir/logar PAN ou PII bruta.

## Notas de Encoding

- Categóricas de alta cardinalidade (email_domain, mcc, merchant_id): WOE/target encoding com CV e smoothing.
- Binários/categóricos estáveis (3DS status, device_channel): one‑hot.
- Numéricos com cauda longa (valor, contagens): `log1p` e padronização por entidade (z‑score) quando aplicável.

---

Este draft serve como contrato inicial de features. Mudanças devem ser versionadas neste arquivo e refletidas no blueprint de extração.

