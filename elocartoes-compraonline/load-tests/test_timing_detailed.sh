#!/bin/bash
# Teste detalhado - 20 requisições com estatísticas

HOST="https://td5i6sx8rh.execute-api.sa-east-1.amazonaws.com"
ENDPOINT="/v1/score"

echo "=============================================="
echo "Teste Detalhado de Tempo de Resposta"
echo "=============================================="
echo ""

declare -a TIMES

for i in $(seq 1 20); do
    TX_ID=$((9100000000 + i))
    UUID1=$(cat /proc/sys/kernel/random/uuid)
    UUID2=$(cat /proc/sys/kernel/random/uuid)
    
    PAYLOAD="{\"nm_payment_system_name\":\"Elo\",\"dt_transaction_date\":\"2026-01-20\",\"transaction_time\":\"11:00:0${i}\",\"id_record\":${TX_ID},\"nm_protocol\":\"2.2.0\",\"cd_device_channel\":1,\"cd_message_category\":1,\"cd_transaction_type\":1,\"nu_pan_bin\":650570,\"nu_pan_last4\":$((2000+i)),\"nm_cardholder_bill_addr_city\":\"São Paulo\",\"nm_cardholder_bill_addr_country\":76.0,\"nm_cardholder_bill_addr_postal_code\":\"01310100\",\"nm_cardholder_bill_addr_state\":\"SP\",\"nm_cardholder_account_information\":\"{\\\"shipNameIndicator\\\":\\\"01\\\"}\",\"cd_acct_type\":1,\"vl_amount\":$((500*i)),\"nu_currency\":986,\"nu_exponent\":2,\"dt_purchase_date_and_time\":\"2026-01-20 11:00:0${i}\",\"nu_acquirer_bin\":5005,\"nm_acquirer_bin\":\"CLOUDWALK\",\"nm_merchant_name\":\"LoadTest\",\"nm_merchant_id\":37432,\"cd_merchant_country\":76,\"nm_merchant_country_name\":\"Brazil\",\"cd_merchant_category_code\":5999,\"cd_tds_trans_id\":\"${UUID1}\",\"nm_issuer\":\"Banco Teste\",\"nu_issuer_bin\":1,\"cd_ds_trans_id\":\"${UUID2}\",\"in_browser_java_enabled\":false,\"in_browser_javascript_enabled\":true,\"nm_browser_language\":\"pt-BR\",\"cd_browser_time_zone\":180,\"nm_browser_user_agent\":\"Mozilla/5.0 LoadTest\",\"in_addr_match_indicator\":\"Y\",\"nm_message_version\":\"2.2.0\",\"flag_autorizacao\":true}"
    
    START=$(date +%s%3N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${HOST}${ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD}")
    END=$(date +%s%3N)
    
    TIME_MS=$((END - START))
    TIMES+=($TIME_MS)
    
    printf "Req %2d | %4d ms | HTTP %s\n" "$i" "$TIME_MS" "$HTTP_CODE"
done

echo ""
echo "=============================================="
echo "ESTATÍSTICAS"
echo "=============================================="

# Calcular estatísticas
MIN=999999
MAX=0
SUM=0

for t in "${TIMES[@]}"; do
    SUM=$((SUM + t))
    [ $t -lt $MIN ] && MIN=$t
    [ $t -gt $MAX ] && MAX=$t
done

AVG=$((SUM / ${#TIMES[@]}))

echo "Total requisições: ${#TIMES[@]}"
echo "Mínimo: ${MIN} ms"
echo "Máximo: ${MAX} ms"
echo "Média:  ${AVG} ms"
echo ""

# Mostrar primeiros 5 vs últimos 5
echo "Primeiras 5 requisições:"
for i in 0 1 2 3 4; do
    echo "  Req $((i+1)): ${TIMES[$i]} ms"
done

echo ""
echo "Últimas 5 requisições:"
for i in 15 16 17 18 19; do
    echo "  Req $((i+1)): ${TIMES[$i]} ms"
done

