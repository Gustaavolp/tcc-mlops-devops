import json
import argparse
from datetime import datetime

class Transformer:
    def parse_date(self, date_str):
        """Converte formato 20251015T14:30:12Z para ISO formatado"""
        if not date_str: return None
        try:
            dt = datetime.strptime(date_str, "%Y%m%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return date_str

    def calculate_amount(self, amount_str, exponent_str):
        try:
            val = float(amount_str)
            exp = int(exponent_str)
            return val / (10 ** exp)
        except (ValueError, TypeError):
            return 0.0

    def map_address(self, addr):
        if not addr:
            return {
                "line1": None, "line2": "", "line3": "",
                "city": None, "state": None, "postal_code": None, "country": None
            }
        
        # Lógica: line1 = Rua, Número
        street = addr.get("street", "")
        number = addr.get("number", "")
        line1 = f"{street}, {number}" if street and number else street

        return {
            "line1": line1,
            "line2": "",
            "line3": "",
            "city": addr.get("city"),
            "state": addr.get("state"),
            "postal_code": addr.get("postal_code"),
            "country": addr.get("country")
        }

    def process(self, input_data):
        # 1. Cálculos Básicos
        amount = self.calculate_amount(input_data.get("purchase_amount"), input_data.get("purchase_exponent", "2"))
        date_iso = self.parse_date(input_data.get("purchase_date"))
        
        # 2. Mapeamento de Canal
        channel_map = {"01": "WEB", "02": "APP"}
        device_channel = channel_map.get(input_data.get("device_channel"), "WEB")

        # 3. Tratamento Cartão
        card_num = input_data.get("card_number", "")
        bin_val = card_num[:8] if len(card_num) >= 8 else None
        last4_val = card_num[-4:] if len(card_num) >= 4 else None

        # 4. Tratamento E-mail
        email = input_data.get("email", "")
        email_parts = email.split("@")
        email_domain = email_parts[1] if len(email_parts) > 1 else None
        email_len = len(email) if email else 0
        domain_type = "corporate"
        
        # User Agent Length
        ua = input_data.get("browser_user_agent", "")
        ua_len = len(ua) if ua else 0

        # 5. Tratamento Datas para Features
        dt_obj = datetime.strptime(input_data.get("purchase_date"), "%Y%m%dT%H:%M:%SZ") if input_data.get("purchase_date") else None
        hour = dt_obj.hour if dt_obj else None
        weekday = dt_obj.weekday() if dt_obj else None # 0=Segunda

        output = {
            "transaction_id": input_data.get("transaction_id"),
            "purchase_date": date_iso,
            "amount": amount,
            "currency": input_data.get("purchase_currency"),
            "device_channel": device_channel,
            "mcc": input_data.get("mcc"),
            "merchant_country_code": input_data.get("merchant_country_code"),
            "bin": bin_val,
            "last4": last4_val,
            "browser_ip": input_data.get("browser_ip"),
            "browser_language": input_data.get("browser_language"),
            "browser_tz": input_data.get("browser_tz"),
            "browser_user_agent": ua,
            "browser_screen_height": input_data.get("browser_screen_height"),
            "browser_screen_width": input_data.get("browser_screen_width"),
            
            "billing_address": self.map_address(input_data.get("billing_address")),
            "shipping_address": self.map_address(input_data.get("shipping_address")),
            
            # Dados que vieram da entrada ou fixos vazios
            "device_info": input_data.get("device_info", {}),
            "acct_info": input_data.get("acct_info", {}),
            "payment_info": input_data.get("payment_info", {}),
            "merchant_risk_indicator": {}, # Fixo vazio
            "mobile_phone": input_data.get("mobile_phone", {}),
            
            "three_ds": {
                "trans_status": input_data.get("three_ds_trans_status"),
                "eci": input_data.get("three_ds_eci"),
                "trans_status_reason": input_data.get("three_ds_trans_status_reason")
            },

            "merchant_document": input_data.get("merchant_document"),
            "cardholder_document": input_data.get("cardholder_document"),
            "card_expiry_date": None,
            "product_type": input_data.get("product_type"),
            "purchase_instal_data": "02", # Fixo conforme exemplo ou input não mapeado
            "fraud_label": 0, # Fixo
            
            "is_direct_selling": input_data.get("is_direct_selling"),
            "is_quick_withdrawal": input_data.get("is_quick_withdrawal"),
            
            # Recorrência (Fixos Null)
            "recurring_amount": None,
            "recurring_currency": None,
            "recurring_frequency": None,
            "recurring_amount_ind": None,
            "recurring_frequency_ind": None,

            # Features Calculadas (f_)
            "f_amount_value": amount,
            "f_installments_count": 2, # Valor fixo/exemplo
            "f_recurring_amount": None,
            "f_recurring_frequency": None,
            "f_is_recurring": 0,
            "f_days_to_expiry": None,
            "f_merchant_id": None,
            "f_cof_number": None,
            "f_cof_number_24h": None,
            "f_cof_number_7d": None,
            "f_device_lat": None,
            "f_device_lon": None,
            "f_delivery_timeframe": None,
            "f_reorder_items_ind": None,
            "f_ship_indicator": None,
            "f_quick_withdrawal": 0,
            
            "f_addr_match": 0,
            "f_diff_country": 0,
            
            "f_day_of_week": weekday,
            "f_is_weekend": 0, # Lógica simplificada

            # Enriched Fields (Fixos Null)
            "enr_card_scheme": None,
            "enr_card_brand": None,
            "enr_card_bank": None,
            "enr_card_country": None,
        }
        return output

# Execução Padrão
if __name__ == "__main__":
    # Exemplo de uso lendo string (simulando arquivo)
    import sys
    import mlflow
    import mlflow.pyfunc
    import pandas as pd

    artifact_uri = "s3://sagemaker-us-east-1-888577064416/12/models/m-eebaca566dc4494dac6e0e5635f06732/artifacts"

    try:
        #mlflow.pyfunc.get_model_dependencies(artifact_uri)
        model = mlflow.pyfunc.load_model(artifact_uri)
    except Exception as e:
        print("Erro ao carregar modelo:", e)

    model = mlflow.pyfunc.load_model(artifact_uri)
    # print("="*60)
    # print(model.metadata.signature)
    # print("="*60)
    # Se quiser testar direto com o JSON que você mandou, 
    # salve o JSON em um arquivo 'input.json' e rode o script.
    try:
        #with open('input.json', 'r', encoding='utf-8') as f:
        with open('input_modelo.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        float_columns = [
            "deviceChannel", "cd_message_category", "cd_transaction_type",
            "bin", "nu_pan_last4", "productType", "vl_amount",
            "nu_currency", "nu_exponent", "eci", "nu_acquirer_bin",
            "merchantCountryCode", "merchantCategoryCode",
            "cd_tds_req_auth_ind", "cd_tds_req_challenge_ind",
            "nu_issuer_bin", "cd_transaction_status_reason_code", "transStatus"
        ]

        for row in data:
            for col in float_columns:
                if col in row and row[col] is not None:
                    row[col] = float(row[col])
            
        transformer = Transformer()
        
        
        # Suporta lista ou objeto único
        #if isinstance(data, list):
        #    result = [transformer.process(item) for item in data]
        #else:
        #    result = transformer.process(data)
            
        # print(json.dumps(result, indent=4, ensure_ascii=False))
        #df = pd.DataFrame(result if isinstance(result, list) else [result])
        df = pd.DataFrame(data if isinstance(data, list) else [data])

        # Inferência
        prediction = model.predict(df)
        print("Prediction:")
        print(prediction)

        
        # Opcional: Salvar em arquivo
        #with open('output.json', 'w', encoding='utf-8') as f:
        #    json.dump(result, f, indent=4, ensure_ascii=False)
            
    except FileNotFoundError:
        print("Crie um arquivo 'input.json' com seus dados para testar.")

        