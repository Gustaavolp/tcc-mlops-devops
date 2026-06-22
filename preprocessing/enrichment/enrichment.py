from user_agents import parse
import pandas as pd

import numpy as np


def enrichment(df : pd.DataFrame, id_user) -> pd.DataFrame:

    parses = df["BROWSER_USER_AGENT"].apply(lambda x: None if pd.isna(x) else parse(x))
    df["nf_enr_user_agent_browser_family"] = parses.apply( lambda x: None if pd.isna(x) else x.browser.family)
    df["nf_enr_user_agent_os_family"] = parses.apply( lambda x: None if pd.isna(x) else x.os.family)
    df["nf_enr_user_agent_device_family"] = parses.apply( lambda x: None if pd.isna(x) else x.device.family)

    df["nf_enr_lang"] = (
        df["BROWSER_LANGUAGE"]
        .apply(lambda x: x.lower() if pd.notna(x) else "")
        .apply(lambda x:
            "pt" if "pt" in x else
            "en" if "en" in x else
            "es" if "es" in x else
            "other"
        )
    )

    df["nf_enr_instalment_payment_data"]  = df["INSTALMENT_PAYMENT_DATA"].fillna(1)

    
    df['nf_enr_period_day'] = np.select (
        [
            df['PURCHASE_DATE_AND_TIME'].dt.hour.between(6, 11),
            df['PURCHASE_DATE_AND_TIME'].dt.hour.between(12, 17),
        ],
        [
            'morning',
            'afternoon',
        ],
        default='night'
    )

    
    df['nf_enr_day_of_week'] = df['PURCHASE_DATE_AND_TIME'].dt.day_name()


    df['nf_seconds_since_last_tx'] = (
    df.groupby(id_user)['PURCHASE_DATE_AND_TIME']
      .diff()
      .dt.total_seconds()
    )
    

    return df

def enrichment_leg_feat(df : pd.DataFrame, id_user : str) -> pd.DataFrame:

    cols_to_lag = ['AMOUNT', 'MERCHANT_COUNTRY', 'MERCHANT_CATEGORY_CODE']
    existing_lag_cols = [c for c in cols_to_lag if c in df.columns]
    for lag in (1, 2, 3):
        for col in existing_lag_cols:
            df[f'nf_feat_lag_{col}_n-{lag}'] = df.groupby(id_user)[col].shift(lag)

    return df
    
    

def behavioral_features_categorial(df:pd.DataFrame, id_user:str) -> pd.DataFrame:

    cs = [

        'MERCHANT_CATEGORY_CODE',
        
        
        "nf_enr_user_agent_browser_family",
        "nf_enr_user_agent_os_family",
        "nf_enr_user_agent_device_family",
        "nf_enr_lang",
        "nf_enr_period_day",
        "nf_enr_day_of_week",

        "CARDHOLDER_BILL_ADDR_CITY",
        "CARDHOLDER_BILL_ADDR_COUNTRY",

        "CARDHOLDER_SHIP_ADDR_CITY",
        "CARDHOLDER_SHIP_ADDR_COUNTRY",

        "MERCHANT_ID",


        "CURRENCY",

    ]


    for c in cs:
      df[f"nf_behaviors_%_{c}"]  =  df.groupby([id_user, c]).cumcount() / df.groupby([id_user]).cumcount()


    return df



def avg_feature(df : pd.DataFrame, id_user : str, N : int):
    
    gb_amount = df.groupby(id_user)["AMOUNT"].rolling(window=N, min_periods=1)

    df[f'nf_amount_mean_last_{N}'] =  gb_amount.mean().reset_index(level=0, drop=True)
    df[f'nf_amount_median_last_{N}'] =  gb_amount.median().reset_index(level=0, drop=True)
    df[f'nf_amount_std_last_{N}'] =  gb_amount.std().reset_index(level=0, drop=True).fillna(0)

    df[f'nf_amount_zscore_{N}'] = (df["AMOUNT"] - df[f'nf_amount_mean_last_{N}'])/df[f'nf_amount_std_last_{N}']

    df[f'nf_amount_zscore_{N}'].fillna(0)

    return df

def select_new_feat(df : pd.DataFrame):
   return [c for c in df.columns if c.startswith('nf_')]


def create_good_feature(df : pd.DataFrame, id_user : str) -> pd.DataFrame:

    df = df.sort_values(by=[id_user, "PURCHASE_DATE_AND_TIME"])

    df = enrichment(df,id_user)
    df = enrichment_leg_feat(df, id_user)
    df = behavioral_features_categorial(df, id_user)

    df = avg_feature(df, id_user, 15)
    df = avg_feature(df, id_user, 10)
    df = avg_feature(df, id_user, 5)

    
    df.drop(columns= [ "nf_enr_user_agent_device_family"])

    return df
