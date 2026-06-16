#!/bin/bash
# Teste de tempo de resposta - 15 requisições sequenciais

HOST="https://td5i6sx8rh.execute-api.sa-east-1.amazonaws.com"
ENDPOINT="/v1/score"

echo "========================================"
echo "Teste de Tempo de Resposta - Staging"
echo "========================================"
echo ""

for i in $(seq 1 15); do
    # Gera ID único para cada requisição
    TX_ID=$((9000000000 + i))
    
    # Payload com ID único
    PAYLOAD=$(cat <<EOFP
{
    "nm_payment_system_name": "Elo",
    "dt_transaction_date": "2026-01-20",
    "transaction_time": "10:00:0${i}",
    "id_record": ${TX_ID},
    "nm_protocol": "2.2.0",
    "cd_device_channel": 1,
    "cd_message_category": 1,
    "cd_transaction_type": 1,
    "nu_pan_bin": 650570,
    "nu_pan_last4": $((1000 + i)),
    "nm_cardholder_bill_addr_city": "São Paulo",
    "nm_cardholder_bill_addr_country": 76.0,
    "nm_cardholder_bill_addr_postal_code": "01310100",
    "nm_cardholder_bill_addr_state": "SP",
    "nm_cardholder_account_information": "{\"shipNameIndicator\":\"01\"}",
    "cd_acct_type": 1,
    "vl_amount": $((1000 * i)),
    "nu_currency": 986,
    "nu_exponent": 2,
    "dt_purchase_date_and_time": "2026-01-20 10:00:0${i}",
    "nu_acquirer_bin": 5005,
    "nm_acquirer_bin": "CLOUDWALK",
    "nm_merchant_name": "Teste LoadTest",
    "nm_merchant_id": 37432,
    "cd_merchant_country": 76,
    "nm_merchant_country_name": "Brazil",
    "cd_merchant_category_code": 5999,
    "cd_tds_trans_id": "$(uuidgen)",
    "nm_issuer": "Banco Teste",
    "nu_issuer_bin": 1,
    "cd_ds_trans_id": "$(uuidgen)",
    "in_browser_java_enabled": false,
    "in_browser_javascript_enabled": true,
    "nm_browser_language": "pt-BR",
    "cd_browser_time_zone": 180,
    "nm_browser_user_agent": "Mozilla/5.0 LoadTest",
    "in_addr_match_indicator": "Y",
    "nm_message_version": "2.2.0",
    "flag_autorizacao": true
}
EOFP
)
    
    # Executa requisição e captura tempo
    START=$(date +%s%3N)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${HOST}${ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD}")
    END=$(date +%s%3N)
    
    # Calcula tempo em ms
    TIME_MS=$((END - START))
    
    # Extrai HTTP code e body
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    # Extrai score do JSON
    SCORE=$(echo "$BODY" | grep -o '"score":[^,}]*' | cut -d: -f2)
    
    printf "Req %2d | %4d ms | HTTP %s | Score: %s\n" "$i" "$TIME_MS" "$HTTP_CODE" "$SCORE"
done

echo ""
echo "========================================"
