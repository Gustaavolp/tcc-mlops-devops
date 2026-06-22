import pandas as pd
import numpy as np
import re
import os
import argparse
from typing import Any, Dict, Optional
from datetime import datetime

pd.options.mode.chained_assignment = None

class FeatureEngineeringService:
    """
    Serviço de Feature Engineering Estático.
    """
    
    def get_user_id(self, row: pd.Series) -> str:
        """
        Define o ID único do usuário.
        Prioridade: Account Info > (BIN + Last4) > ID Record
        """
        acc_info = row.get('nm_cardholder_account_information')
        if pd.notna(acc_info) and str(acc_info).strip():
            return re.sub(r"\D", "", str(acc_info))
            
        bin_num = str(row.get('nu_pan_bin', '') or row.get('bin', ''))
        last4 = str(row.get('nu_pan_last4', ''))
        if bin_num and last4:
            return f"{bin_num}{last4}"
            
        return str(row.get('id_record', row.get('cardHolderDocument', 'unknown')))

    def extract_device_os(self, user_agent: str) -> str:
        """Extrai Sistema Operacional."""
        if pd.isna(user_agent): return "unknown"
        ua = str(user_agent).lower()
        
        if "android" in ua: return "android"
        if "iphone" in ua or "ipad" in ua: return "ios"
        if "windows" in ua: return "windows"
        if "mac os" in ua: return "mac"
        if "linux" in ua: return "linux"
        return "other"

    def enrich_row(self, row: pd.Series) -> pd.Series:
        """Aplica features estáticas linha a linha."""
        
        user_agent = row.get("nm_browser_user_agent") or row.get("browserUserAgent")
        payment_system = str(row.get('paymentSystem', '')).lower()

        is_elo = 1 if 'elo' in payment_system else 0
        
        device_os = self.extract_device_os(user_agent)
        
        bill_state = str(row.get('nm_cardholder_bill_addr_state', '') or row.get('billAddrState', '')).upper().strip()
        ship_state = str(row.get('nm_cardholder_ship_addr_state', '') or row.get('shipAddrState', '')).upper().strip()
        addr_mismatch = 1 if (bill_state and ship_state and bill_state != ship_state) else 0

        user_id = self.get_user_id(row)

        return pd.Series({
            "enr_is_elo": is_elo,
            "enr_card_bank": row.get('nm_issuer'),
            "enr_card_type": row.get('cd_acct_type') or row.get('productType'),
            "enr_device_os": device_os,
            "enr_addr_mismatch": addr_mismatch,
            "enr_user_id": user_id
        }, dtype='object')

def calculate_rolling_features(df_group: pd.DataFrame) -> pd.DataFrame:
    """Calcula features de histórico (Janela Deslizante)."""
    purchase_amount = pd.to_numeric(df_group['vl_amount'], errors='coerce')
    
    rolling = purchase_amount.rolling(window=10, min_periods=1)
    
    return pd.DataFrame({
        'feat_user_tx_count_10': rolling.count().shift(1).fillna(0).astype(int),
        'feat_user_tx_sum_10': rolling.sum().shift(1).fillna(0).round(2),
        'feat_user_avg_amount_10': rolling.mean().shift(1).round(2),
        'feat_user_std_amount_10': rolling.std().shift(1).fillna(-1).round(2)
    })

def process_gold_layer(input_path: str, output_path: str):
    print(f"Iniciando Geração da Camada Ouro (Otimizada)...")
    print(f"Input: {input_path}")

    try:
        df = pd.read_csv(input_path, encoding='latin1', dtype=str)
        if df.shape[1] <= 1:
             df = pd.read_csv(input_path, sep=';', encoding='latin1', dtype=str)
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return

    if 'vl_amount' in df.columns:
        df['vl_amount'] = pd.to_numeric(df['vl_amount'], errors='coerce').fillna(0)

    print("Executando Feature Engineering Estático...")
    fe_service = FeatureEngineeringService()
    df_enriched_cols = df.apply(fe_service.enrich_row, axis=1)
    df_working = pd.concat([df, df_enriched_cols], axis=1)

    print("Preparando Série Temporal...")
    if 'purchaseDate' in df_working.columns:
        df_working['purchaseDateTime'] = pd.to_datetime(df_working['purchaseDate'], errors='coerce')
    elif 'dt_purchase_date_and_time' in df_working.columns:
        df_working['purchaseDateTime'] = pd.to_datetime(df_working['dt_purchase_date_and_time'], errors='coerce')
    else:
        print("Aviso: Data não encontrada. Usando índice.")
        df_working['purchaseDateTime'] = df_working.index

    df_working.sort_values(by=['enr_user_id', 'purchaseDateTime'], inplace=True)

    print("Gerando Lag Features (n-1, n-2, n-3)...")
    cols_to_lag = ['vl_amount', 'merchantCountryCode', 'merchantCategoryCode'] 
    existing_lag_cols = [c for c in cols_to_lag if c in df_working.columns]
    
    for lag in [1, 2, 3]:
        for col in existing_lag_cols:
            new_col = f'feat_lag_{col}_n-{lag}'
            df_working[new_col] = df_working.groupby('enr_user_id')[col].shift(lag)

    if pd.api.types.is_datetime64_any_dtype(df_working['purchaseDateTime']):
        df_working['feat_time_since_last_tx_sec'] = df_working.groupby('enr_user_id')['purchaseDateTime'].diff().dt.total_seconds().fillna(-1)
    else:
        df_working['feat_time_since_last_tx_sec'] = -1

    print("Calculando Métricas de Histórico...")
    df_rolling = df_working.groupby('enr_user_id', dropna=False).apply(calculate_rolling_features).reset_index(level=0, drop=True)
    df_gold = pd.concat([df_working, df_rolling], axis=1)

    print("Aplicando Frequency Encoding...")
    cols_freq = ['merchantCountryCode', 'enr_card_bank', 'billAddrState', 'browserLanguage'] # Nomes padronizados na Prata
    for col in cols_freq:
        if col in df_gold.columns:
            freq_map = df_gold[col].value_counts(normalize=True)
            df_gold[f'feat_freq_{col}'] = df_gold[col].map(freq_map).fillna(0)

    if 'purchaseDateTime' in df_gold.columns:
        df_gold.drop(columns=['purchaseDateTime', 'paymentSystem', 'browserUserAgent'], inplace=True)
    
    cols_lags = [c for c in df_gold.columns if 'feat_' in c]
    for c in cols_lags:
        df_gold[c] = df_gold[c].fillna(-1)
    
    df_gold = df_gold.fillna('')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_gold.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Sucesso! Camada Ouro salva em: {output_path}")
    print(f"Features Geradas: {len([c for c in df_gold.columns if 'feat_' in c or 'enr_' in c])}")


if __name__ == "__main__":
    process_gold_layer("silver.csv", "./gold.csv")