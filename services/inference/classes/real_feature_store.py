import boto3
import os
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from boto3.dynamodb.conditions import Key
from user_agents import parse

REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("DYNAMO_TABLE", "elo-fraud-customer-recent-tx-dev")

class OnlineFeatureStore:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource("dynamodb", region_name=REGION)
            self.table = self.dynamodb.Table(TABLE_NAME)
        except Exception as e:
            logging.error(f"❌ Falha ao conectar no DynamoDB: {e}")
            self.table = None

        self.lag_columns = ['AMOUNT', 'MERCHANT_COUNTRY', 'MERCHANT_CATEGORY_CODE']
        self.rolling_windows = [15, 10, 5]
        self.behavioral_cols = [
            'MERCHANT_CATEGORY_CODE', "nf_enr_user_agent_browser_family",
            "nf_enr_user_agent_os_family", "nf_enr_user_agent_device_family", "nf_enr_lang", "nf_enr_period_day",
            "nf_enr_day_of_week", "CARDHOLDER_BILL_ADDR_CITY",
            "CARDHOLDER_BILL_ADDR_COUNTRY", "CARDHOLDER_SHIP_ADDR_CITY",
            "CARDHOLDER_SHIP_ADDR_COUNTRY", "MERCHANT_ID", "CURRENCY"
        ]

    def _parse_dynamo_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converte item do histórico do Dynamo para chaves padronizadas (UPPER_CASE)"""
        p = item.get("payload", {}) 
        if not isinstance(p, dict): p = {}
        
        # Mapeie aqui como você salvou no Dynamo para como o modelo lê hoje
        return {
            "AMOUNT": float(p.get("AMOUNT") or p.get("purchaseAmount") or 0.0),
            "MERCHANT_COUNTRY": str(p.get("MERCHANT_COUNTRY") or p.get("merchantCountryCode") or ""),
            "MERCHANT_CATEGORY_CODE": str(p.get("MERCHANT_CATEGORY_CODE") or p.get("mcc") or ""),
            "PURCHASE_DATE_AND_TIME": item.get("timestamp") or p.get("PURCHASE_DATE_AND_TIME"),
            "CURRENCY": str(p.get("CURRENCY") or ""),
            "MERCHANT_ID": str(p.get("MERCHANT_ID") or ""),
            "nf_enr_user_agent_browser_family": p.get("nf_enr_user_agent_browser_family"),
            "nf_enr_user_agent_os_family": p.get("nf_enr_user_agent_os_family"),
        }

    def _enrich_stateless(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Any]:
        """Cálculos que não dependem do banco de dados"""
        p = payload.copy()
        
        ua_str = p.get("BROWSER_USER_AGENT")
        if ua_str:
            try:
                ua = parse(ua_str)
                p["nf_enr_user_agent_browser_family"] = ua.browser.family
                p["nf_enr_user_agent_os_family"] = ua.os.family
                p["nf_enr_user_agent_device_family"] = ua.device.family
            except:
                p["nf_enr_user_agent_browser_family"] = None
                p["nf_enr_user_agent_os_family"] = None
                p["nf_enr_user_agent_device_family"] = None
        else:
            p["nf_enr_user_agent_browser_family"] = None
            p["nf_enr_user_agent_os_family"] = None
            p["nf_enr_user_agent_device_family"] = None

        lang = str(p.get("BROWSER_LANGUAGE", "")).lower()
        if "pt" in lang: p["nf_enr_lang"] = "pt"
        elif "en" in lang: p["nf_enr_lang"] = "en"
        elif "es" in lang: p["nf_enr_lang"] = "es"
        else: p["nf_enr_lang"] = "other"

        raw_dt = p.get("PURCHASE_DATE_AND_TIME")
        dt_obj = None
        try:
            if raw_dt:
                dt_obj = pd.to_datetime(raw_dt)
                hour = dt_obj.hour
                if 6 <= hour <= 11: p["nf_enr_period_day"] = "morning"
                elif 12 <= hour <= 17: p["nf_enr_period_day"] = "afternoon"
                else: p["nf_enr_period_day"] = "night"
                
                p["nf_enr_day_of_week"] = dt_obj.day_name()
            else:
                p["nf_enr_period_day"] = "night"
                p["nf_enr_day_of_week"] = None
        except:
             p["nf_enr_period_day"] = "night"
             p["nf_enr_day_of_week"] = None

        inst = p.get("INSTALMENT_PAYMENT_DATA")
        p["nf_enr_instalment_payment_data"] = float(inst) if inst is not None else 1.0

        return p, dt_obj

    def _enrich_stateful(self, payload: Dict[str, Any], history: List[Dict[str, Any]], current_dt) -> Dict[str, Any]:
        """Cálculos baseados no histórico recuperado"""
        p = payload.copy()
        
        current_amt = float(p.get("AMOUNT") or 0.0)
        hist_amounts = [float(h.get("AMOUNT") or 0.0) for h in history]
        full_amounts = [current_amt] + hist_amounts 

        for N in self.rolling_windows:
            window = full_amounts[:N]
            if not window:
                p[f'nf_amount_mean_last_{N}'] = 0.0
                p[f'nf_amount_median_last_{N}'] = 0.0
                p[f'nf_amount_std_last_{N}'] = 0.0
                p[f'nf_amount_zscore_{N}'] = 0.0
                continue
            
            mean_val = np.mean(window)
            std_val = np.std(window, ddof=1) if len(window) > 1 else 0.0
            
            p[f'nf_amount_mean_last_{N}'] = float(mean_val)
            p[f'nf_amount_median_last_{N}'] = float(np.median(window))
            p[f'nf_amount_std_last_{N}'] = float(std_val)
            
            zscore = 0.0
            if std_val > 0:
                zscore = (current_amt - mean_val) / std_val
            p[f'nf_amount_zscore_{N}'] = float(zscore)

        for lag in [1, 2, 3]:
            idx = lag - 1
            item = history[idx] if len(history) > idx else {}
            for col in self.lag_columns:
                p[f'nf_feat_lag_{col}_n-{lag}'] = item.get(col)

        p['nf_seconds_since_last_tx'] = None
        if current_dt and history:
            try:
                last_raw = history[0].get("PURCHASE_DATE_AND_TIME")
                last_dt = pd.to_datetime(last_raw, unit='s' if isinstance(last_raw, (int, float)) else None)
                diff = (current_dt - last_dt).total_seconds()
                p['nf_seconds_since_last_tx'] = float(diff)
            except:
                pass

        total_tx = len(history) + 1
        for col in self.behavioral_cols:
            val = p.get(col)
            if val is None:
                p[f"nf_behaviors_%_{col}"] = 0.0
                continue
            count = sum(1 for h in history if h.get(col) == val)
            p[f"nf_behaviors_%_{col}"] = (count + 1) / total_tx

        return p

    def enrich_payload(self, normalized_payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = normalized_payload.get("CARDHOLDER_ACCOUNT_IDENTIFIER")
        
        enriched_p, current_dt = self._enrich_stateless(normalized_payload)

        history = []
        if user_id and self.table:
            try:
                resp = self.table.query(
                    KeyConditionExpression=Key("acctID").eq(str(user_id)),
                    ScanIndexForward=False,
                    Limit=20
                )
                items = resp.get("Items", [])
                history = [self._parse_dynamo_item(i) for i in items]
            except Exception as e:
                logging.error(f"Erro DynamoDB: {e}")

        final_payload = self._enrich_stateful(enriched_p, history, current_dt)
        
        return final_payload