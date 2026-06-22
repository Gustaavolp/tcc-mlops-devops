import pandas as pd
import numpy as np
import argparse
import os
from pathlib import Path
from datetime import datetime

COLUMN_MAPPING = {
    # Valores e Identificadores
    'nu_pan_bin': 'bin',
    'id_record': 'cardHolderDocument',
    'cd_acct_type': 'productType',
    'nm_payment_system_name': 'paymentSystem',
    
    # Contexto da Transação
    'cd_device_channel': 'deviceChannel',
    'nm_results_status': 'transStatus',
    'cd_merchant_category_code': 'merchantCategoryCode',
    'cd_merchant_country': 'merchantCountryCode',
    
    # Dados do Navegador
    'nm_browser_user_agent': 'browserUserAgent',
    'nm_browser_language': 'browserLanguage',
    'cd_browser_time_zone': 'browserTZ',
    
    # Endereços (Billing)
    'nm_cardholder_bill_addr_city': 'billAddrCity',
    'nm_cardholder_bill_addr_state': 'billAddrState',
    'nm_cardholder_bill_addr_country': 'billAddrCountry',
    'nm_cardholder_bill_addr_postal_code': 'billAddrPostCode',
    
    # Endereços (Shipping)
    'nm_cardholder_ship_addr_city': 'shipAddrCity',
    'nm_cardholder_ship_addr_state': 'shipAddrState',
    'nm_cardholder_ship_addr_country': 'shipAddrCountry',
    'nm_cardholder_ship_addr_postal_code': 'shipAddrPostCode',
    
    # 3DS Específico
    'cd_eci': 'eci',
    'cd_interaction_ctr': 'interactionCounter'
}

COLUMNS_TO_DROP = [
    'nm_tds_url', 'nm_merchant_url', 'nm_ds_url', 'nm_acs_url', 'nm_notification_url',
    'nm_sdk_trans_id', 'nm_sdk_app_id', 'cd_tds_trans_id', 'cd_ds_trans_id',
    'nm_acs_trans_id', 'nm_serial_number', 'nm_sdk_ref_number',
    'nm_acs_start_protocol_ver', 'nm_acs_end_protocol_ver', 'nm_message_version',
    'nu_exponent', 'nm_card_range_data', 'nm_dss_ref_number', 'nm_server_trans_id',
    'nm_three_ds_server_trans_id', 'nm_card_token_exp_date', 'nm_cardholder_information_text',
    'vl_total', 'nm_acquirer'

    #nm_acquirer_bin, nu_acquirer_bin
]


def count_unique_values(df):
    for col in df.columns:
        try:
            unique_count = df[col].nunique(dropna=False)
            print(f"Coluna '{col}': {unique_count} valores diferentes")
        except Exception as e:
            print(f"Erro ao processar a coluna '{col}': {e}")


def clean_currency(value):
    if pd.isna(value) or str(value).strip() == '':
        return 0.0
        
    s = str(value).strip()
    s = s.replace('R$', '').strip()
    
    try:
        if ',' in s:
            s = s.replace('.', '')
            s = s.replace(',', '.')
            return float(s)
            
        if '.' in s:
            return float(s)
            
        if s.replace('-', '').isdigit():
            return float(s) / 100.0
            
        return 0.0
    except ValueError:
        return 0.0

def process_file(input_file, output_file):
    print(f"Iniciando limpeza bruta...")
    print(f"Lendo arquivo: {input_file}")

    try:
        df = pd.read_csv(input_file, sep=';', encoding='latin1', dtype=str, nrows = 300000)
    
        if len(df.columns) <= 1:
            print("Separador ';' parece incorreto. Tentando ','...")
            df = pd.read_csv(input_file, sep=',', encoding='latin1', dtype=str, nrows = 300000)
            
        print(f"   -> Dimensões Originais: {df.shape}")

    except Exception as e:
        print(f"Erro crítico ao ler arquivo: {e}")
        return
    print(count_unique_values(df))

    print("Padronizando nomes de colunas...")
    df.rename(columns=COLUMN_MAPPING, inplace=True)

    if 'vl_amount' in df.columns:
        df['vl_amount'] = df['vl_amount'].apply(clean_currency)
    else:
        df['vl_amount'] = 0.0

    if 'dt_transaction_date' in df.columns and 'transaction_time' in df.columns:
        df['purchaseDate'] = df['dt_transaction_date'] + ' ' + df['transaction_time']
        df.drop(columns=['dt_transaction_date', 'transaction_time'], inplace=True)
    elif 'dt_purchase_date_and_time' in df.columns:
        df['purchaseDate'] = df['dt_purchase_date_and_time']

    if 'fraud_label' not in df.columns:
        df['fraud_label'] = 0

    print("Removendo colunas técnicas desnecessárias...")
    drop_cols = [c for c in COLUMNS_TO_DROP if c in df.columns]
    df.drop(columns=drop_cols, inplace=True)

    print(f"Salvando arquivo limpo em: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Processo concluído! {df.shape[0]} linhas processadas.")



if __name__ == "__main__":
    process_file("transaction_3ds_202511252117.csv", "./silver.csv")