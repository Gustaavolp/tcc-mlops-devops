import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from classes.real_feature_store import RealFeatureStore

class FeatureEngineeringService:
    def __init__(self):
        self.feature_store = RealFeatureStore()
        
        self.default_values = {
            "Float64": 0.0,
            "Int64": 0,
            "boolean": False,
            "string": "unknown",
            "datetime64[ns, UTC]": datetime.now()
        }
        
        self.schema_types = {
            "feat_user_avg_purchases_per_day_hist": "Float64",
            "feat_user_amount_std_hist": "Float64",
            "feat_user_amount_z_hist": "Float64",
            "feat_user_amount_mean_hist": "Float64",
            "feat_user_amount_q95_hist": "Float64",
            "feat_user_tx_sum_10": "Float64",
            "feat_time_since_last_tx_sec": "Float64",
            "feat_user_avg_amount_10": "Float64",
            "feat_user_std_amount_10": "Float64",
            "feat_amount_major": "Float64",
            "feat_lag_vl_amount_n-1": "Float64",
            "feat_lag_vl_amount_n-2": "Float64",
            "feat_lag_vl_amount_n-3": "Float64",
            "feat_diff_transaction_purchase": "Float64",
            "feat_freq_nm_browser_language": "Float64",
            "feat_freq_nm_cardholder_bill_addr_state": "Float64",
            "feat_freq_cd_merchant_country": "Float64",
            "feat_freq_enr_card_bank": "Float64",
            "nm_instalment_payment_data": "Float64",
            "feat_purchase_weekday": "string",
            "feat_transaction_weekday": "string",
            "cd_device_channel": "Float64",
            "in_tds_req_decoupled_ind": "Float64",
            "feat_user_tx_count_total": "Float64",
            "feat_merchant_fraud_count_hist": "Float64",
            "feat_user_fraud_count_hist": "Float64",
            "feat_user_tx_count_10": "Float64",
            "nm_acs_challenge_mandated_ind": "boolean",
            "in_browser_java_enabled": "boolean",
            "in_browser_javascript_enabled": "boolean",
            "in_addr_match_indicator": "boolean",
            "in_completed": "boolean",
            "flag_autorizacao": "boolean",
            "flag_fraude": "boolean",
            "enr_addr_mismatch": "boolean",
            "feat_has_installment": "boolean",
            "feat_user_has_fraud_history": "boolean",
            "feat_merchant_has_fraud_hist": "boolean",
            "feat_user_is_high_amount": "boolean",
            "enr_is_elo": "boolean",
            "dt_transaction_datetime": "datetime64[ns, UTC]",
            "nu_recurring_expiry": "string",
            "cd_merchant_category_code": "string",
            "nm_browser_language": "string",
            "nu_acquirer_bin": "string",
            "nm_cardholder_bill_addr_country": "string",
            "nm_merchant_country_name": "string",
            "nm_cardholder_bill_addr_state": "string",
            "nm_tds_server_oper_id": "string",
            "nm_cardholder_ship_addr_state": "string",
            "dc_error_description": "string",
            "nm_cardholder_ship_addr_country": "string",
            "cd_merchant_country": "string",
            "feat_lag_cd_merchant_country_n-1": "string",
            "cd_browser_time_zone": "string",
            "feat_lag_cd_merchant_country_n-2": "string",
            "feat_lag_cd_merchant_country_n-3": "string",
            "nu_currency": "string",
            "cd_interaction_ctr": "string",
            "nm_dss_ref_number": "string",
            "nu_issuer_bin": "string",
            "enr_card_bank": "string",
            "nm_transaction_status_reason": "string",
            "nm_acquirer_bin": "string",
            "nm_acs_url": "string",
            "cd_error_code": "string",
            "nm_final_status": "string",
            "cd_transaction_status": "string",
            "cd_tds_req_challenge_ind": "string",
            "cd_transaction_status_reason_code": "string",
            "nm_auth_method": "string",
            "nm_sdk_ref_number": "string",
            "cd_tds_req_auth_ind": "string",
            "cd_challenge_cancel_ind": "string",
            "nm_flow": "string",
            "nm_transaction_status_code": "string",
            "cd_eci": "string",
            "nm_ds_url": "string",
            "enr_card_type": "string",
            "cd_transaction_type": "string",
            "nm_results_status": "string",
            "enr_device_os": "string",
            "cd_message_category": "string",
            "nm_tds_method_completion_ind": "string",
            "nm_acs_ref_number": "string",
            "nm_acs_operator_id": "string",
            "nm_acs_rendering_type": "string",
            "nm_auth_type": "string",
            "feat_purchase_time_bin": "string",
            "feat_transaction_time_bin": "string",
            "dataset_flag": "string",
            "nm_protocol": "string",
            "nm_ds_ref_number": "string",
            "nm_acs_start_protocol_ver": "string",
            "nm_acs_end_protocol_ver": "string",
            "nm_message_version": "string"
        }

    def _clean_currency(self, value: Any, exponent: Any = None) -> float:
        """Limpeza 'Nuclear' de moeda."""
        if value is None or str(value).strip() == "": return 0.0
        s_raw = str(value).strip()
        try:
            s = re.sub(r'\s*\(.*?\)', '', s_raw)
            s = re.sub(r'[A-Z]{3}', '', s)
            s = s.replace("R$", "").replace("$", "").strip()
            
            if exponent is not None and str(exponent).strip().isdigit():
                clean_nums = re.sub(r'[^\d-]', '', s) 
                if clean_nums: return float(clean_nums) / (10 ** int(exponent))

            if "," in s: return float(s.replace(".", "").replace(",", "."))
            if "." in s and s.count(".") == 1: return float(s)
            
            if re.match(r'^-?\d+$', s): return float(s) / 100.0
            
            return float(s)
        except:
            print(f"AVISO: Falha ao converter moeda '{value}'")
            return 0.0

    def _parse_date(self, date_str: Any) -> datetime:
        if not date_str: return datetime.now()
        try:
            clean_str = str(date_str).replace("Z", "").replace("T", " ").split(".")[0]
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d%H%M%S"]:
                try: return datetime.strptime(clean_str, fmt)
                except ValueError: continue
            return datetime.fromisoformat(clean_str)
        except: return datetime.now()

    def _to_float(self, val: Any) -> float:
        try: return float(val)
        except: return 0.0

    def _to_int(self, val: Any) -> int:
        try: return int(float(val))
        except: return 0

    def _to_bool(self, val: Any) -> bool:
        if isinstance(val, bool): return val
        s = str(val).lower()
        return s in ["true", "1", "s", "y", "yes"]

    def _to_str(self, val: Any) -> str:
        if val is None: return "unknown"
        s = str(val).strip()
        return s if s else "unknown"

    def get_user_id(self, payload: Dict[str, Any]) -> str:
        # Prioridade 1: ID de Conta
        acc = payload.get("nm_cardholder_account_information")
        if acc: return re.sub(r"\D", "", str(acc))
        # Prioridade 2: Documento
        doc = payload.get("cardHolderDocument") or payload.get("id_record")
        if doc: return re.sub(r"\D", "", str(doc))
        return "unknown"

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        output = {} 
        
        # 1. Extração de Dados Críticos (Moeda e Data) com limpeza pesada
        raw_amount = input_data.get("vl_total") or input_data.get("vl_amount") or input_data.get("amount") or input_data.get("purchase_amount")
        raw_exp = input_data.get("nu_exponent") or input_data.get("purchase_exponent")
        vl_amount = self._clean_currency(raw_amount, raw_exp)
        
        raw_date = input_data.get("dt_transaction_datetime") or input_data.get("dt_purchase_date_and_time") or input_data.get("purchase_date")
        dt_obj = self._parse_date(raw_date)

        # 2. Features Calculadas / Derivadas (Estáticas)
        installments = self._to_float(input_data.get("nm_instalment_payment_data") or input_data.get("purchaseInstalData"))
        is_elo = "elo" in str(input_data.get("nm_payment_system_name", "")).lower()
        
        user_agent = str(input_data.get("nm_browser_user_agent", "")).lower()
        if "android" in user_agent: os_dev = "android"
        elif "iphone" in user_agent or "ipad" in user_agent: os_dev = "ios"
        elif "windows" in user_agent: os_dev = "windows"
        else: os_dev = "other"

        bill_state = self._to_str(input_data.get("nm_cardholder_bill_addr_state")).upper()
        ship_state = self._to_str(input_data.get("nm_cardholder_ship_addr_state")).upper()
        addr_mismatch = (bill_state != "UNKNOWN" and ship_state != "UNKNOWN" and bill_state != ship_state)

        hour = dt_obj.hour
        time_bin = "DAWN" if 0 <= hour < 6 else "MORNING" if 6 < 12 else "AFTERNOON" if 12 < 18 else "NIGHT"

        # 3. Preenchimento Inicial com Dados Calculados
        output["feat_amount_major"] = vl_amount
        output["dt_transaction_datetime"] = dt_obj
        output["nm_instalment_payment_data"] = installments
        output["feat_has_installment"] = installments > 1
        output["enr_is_elo"] = is_elo
        output["enr_device_os"] = os_dev
        output["enr_addr_mismatch"] = addr_mismatch
        output["nm_cardholder_bill_addr_state"] = bill_state
        output["nm_cardholder_ship_addr_state"] = ship_state
        
        output["feat_purchase_weekday"] = float(dt_obj.weekday())
        output["feat_transaction_weekday"] = float(dt_obj.weekday())
        output["feat_purchase_time_bin"] = time_bin
        output["feat_transaction_time_bin"] = time_bin
        output["dataset_flag"] = "inference"

        # Tenta copiar campos diretos do input se baterem o nome
        for key, dtype in self.schema_types.items():
            if key in input_data and key not in output:
                if dtype == "Float64": output[key] = self._to_float(input_data[key])
                elif dtype == "Int64": output[key] = self._to_int(input_data[key])
                elif dtype == "boolean": output[key] = self._to_bool(input_data[key])
                else: output[key] = self._to_str(input_data[key])

        # 4. Enriquecimento Feature Store (DynamoDB)
        user_id = self.get_user_id(input_data)
        
        # Chaves auxiliares para o Worker salvar depois
        output["enr_user_doc_id"] = user_id 
        output["cardHolderDocument"] = user_id 

        try:
            hist_features = self.feature_store.enrich_payload(output)
            output.update(hist_features)
        except Exception as e:
            print(f"Erro Feature Store: {e}")

        # 5. ENFORCE SCHEMA FINAL (Garante integridade para o Modelo)
        final_payload = {}
        
        # Copia chaves auxiliares (Pass-through para o SQS/Dynamo)
        final_payload["enr_user_doc_id"] = output.get("enr_user_doc_id")
        final_payload["cardHolderDocument"] = output.get("cardHolderDocument")
        final_payload["transaction_id"] = input_data.get("transaction_id") or input_data.get("id_record")
        final_payload["amount"] = vl_amount # Para log humano

        # Itera sobre o Schema e preenche tudo
        for key, dtype in self.schema_types.items():
            val = output.get(key)
            
            if val is None:
                final_payload[key] = self.default_values.get(dtype)
            else:
                if dtype == "Float64": final_payload[key] = self._to_float(val)
                elif dtype == "Int64": final_payload[key] = self._to_int(val)
                elif dtype == "boolean": final_payload[key] = self._to_bool(val)
                elif dtype == "string": final_payload[key] = self._to_str(val)
                elif "datetime" in dtype: final_payload[key] = val
                else: final_payload[key] = val

        return final_payload