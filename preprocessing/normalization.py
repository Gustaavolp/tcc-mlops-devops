import pandas as pd
import numpy as np
import json


from enrichment.enrichment import create_good_feature, select_new_feat

di = {

    "CARDHOLDER_ACCOUNT_IDENTIFIER"	 : ("acctID"	,"Identificador adicional da conta do portador"),
    "CARDHOLDER_ACCOUNT_INFORMATION__shipNameIndicator"	 : ("acctInfo.shipNameIndicator"	,"Indica se o nome do frete difere do nome da conta"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccAgeInd"	 : ("acctInfo.chAccAgeInd"	,"Indicador da idade da conta do comprador"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccDate"	 : ("acctInfo.chAccDate"	,"Data de criação da conta"),
    "CARDHOLDER_ACCOUNT_INFORMATION__nbPurchaseAccount"	 : ("acctInfo.nbPurchaseAccount"	,"Número de compras realizadas"),
    "CARDHOLDER_ACCOUNT_INFORMATION__txnActivityDay"	 : ("acctInfo.txnActivityDay"	,"Nº transações no dia"),
    "CARDHOLDER_ACCOUNT_INFORMATION__txnActivityYear"	 : ("acctInfo.txnActivityYear"	,"Nº transações no ano"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccChange"	 : ("acctInfo.chAccChange"	,"Data da última mudança cadastral (YYYYMMDD)"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccChangeInd"	 : ("acctInfo.chAccChangeInd"	,"Indicador de mudança cadastral"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccPwChange"	 : ("acctInfo.chAccPwChange"	,"Data da última troca de senha"),
    "CARDHOLDER_ACCOUNT_INFORMATION__chAccPwChangeInd"	 : ("acctInfo.chAccPwChangeInd"	,"Indicador da troca de senha"),
    "CARDHOLDER_ACCOUNT_INFORMATION__provisionAttemptsDay"	 : ("acctInfo.provisionAttemptsDay"	,"Nº de tentativas de provisionamento no dia"),
    "CARDHOLDER_ACCOUNT_INFORMATION__paymentAccAge"	 : ("acctInfo.paymentAccAge"	,"Data de criação da conta de pagamento"),
    "CARDHOLDER_ACCOUNT_INFORMATION__paymentAccInd"	 : ("acctInfo.paymentAccInd"	,"Indicador da conta de pagamento"),
    "CARDHOLDER_ACCOUNT_INFORMATION__suspiciousAccActivity"	 : ("acctInfo.suspiciousAccActivity"	,"Indica atividade suspeita na conta"),
    "ACCT_NUMBER"	 : ("acctNumber"	,"Número da conta do portador / cartão"),
    "ACCT_TYPE"	 : ("acctType"	,"Tipo da conta"),
    "ACQUIRER_BIN"	 : ("acquirerBIN"	,"BIN do adquirente"),
    "MERCHANT_ID"	 : ("acquirerMerchantID"	,"ID do lojista no adquirente"),
    "ADDR_MATCH_INDICATOR"	 : ("addrMatch"	,"Indica se billing == shipping"),
    "CARDHOLDER_BILL_ADDR_CITY"	 : ("billAddrCity"	,"Cidade do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_COUNTRY"	 : ("billAddrCountry"	,"País do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_LINE1"	 : ("billAddrLine1"	,"Linha 1 do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_LINE2"	 : ("billAddrLine2"	,"Linha 2 do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_LINE3"	 : ("billAddrLine3"	,"Linha 3 do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_POSTAL_CODE"	 : ("billAddrPostCode"	,"CEP do endereço de cobrança"),
    "CARDHOLDER_BILL_ADDR_STATE"	 : ("billAddrState"	,"Estado do endereço de cobrança"),
    "BROWSER_JAVA_ENABLED"	 : ("browserJavaEnabled"	,"Java está habilitado?"),
    "BROWSER_JAVASCRIPT_ENABLED"	 : ("browserJavascriptEnabled"	,"Javascript está habilitado?"),
    "BROWSER_LANGUAGE"	 : ("browserLanguage"	,"Idioma do navegador"),
    "BROWSER_TIME_ZONE"	 : ("browserTZ"	,"Timezone do navegador (minutos)"),
    "BROWSER_USER_AGENT"	 : ("browserUserAgent"	,"User-agent do navegador"),
    "CARD_TOKEN_EXP_DATE"	 : ("cardExpiryDate"	,"Data de expiração do cartão (YYMM)"),
    "CARDHOLDER_NAME"	 : ("cardholderName"	,"Nome do portador do cartão"),
    "DEVICE_CHANNEL"	 : ("deviceChannel"	,"Canal do dispositivo utilizado na autenticação (01=App, 02=Browser, 03=3RI)"),
    "DEVICE_INFO"	 : ("deviceInfo"	,"Dados do dispositivo coletados pelo comerciante/SDK"),
    "CARDHOLDER_EMAIL_ADDRESS"	 : ("email"	,"E-mail do portador"),
    "MERCHANT_CATEGORY_CODE"	 : ("mcc"	,"MCC do estabelecimento"),
    "MERCHANT_COUNTRY"	 : ("merchantCountryCode"	,"País do comerciante"),
    "MERCHANT_NAME"	 : ("merchantName"	,"Nome do comerciante"),
    "MERCHANT_RISK_IND__deliveryEmailAddress"	 : ("merchantRiskIndicator.deliveryEmailAddress"	,"E-mail de entrega"),
    "MERCHANT_RISK_IND__deliveryTimeframe"	 : ("merchantRiskIndicator.deliveryTimeframe"	,"Tempo estimado de entrega"),
    "MERCHANT_RISK_IND__shipIndicator"	 : ("merchantRiskIndicator.shipIndicator"	,"Indicador de tipo de entrega"),
    "MERCHANT_RISK_IND__preOrderPurchaseInd"	 : ("merchantRiskIndicator.preOrderPurchaseInd"	,"Indicador de pré-pedido"),
    "MESSAGE_CATEGORY"	 : ("merchantRiskIndicatorpreOrderPurchaseInd	Indicador de pré-pedido"),
    "MESSAGE_VERSION"	 : ("messageCategory"	,"Categoria da mensagem (01=PA, 02=NPA)"),
    "AMOUNT"	 : ("purchaseAmount"	,"Valor total da compra em centavos (sem separador decimal)"),
    "CURRENCY"	 : ("purchaseCurrency"	,"Código da moeda ISO 4217 (ex.: 986 = BRL)"),
    "PURCHASE_DATE_AND_TIME"	 : ("purchaseDate"	,"Data/hora da compra (YYYYMMDDHHMMSS)"),
    "EXPONENT"	 : ("purchaseExponent"	,"Expoente da moeda (ex.: 2 = duas casas decimais)"),
    "INSTALMENT_PAYMENT_DATA"	 : ("purchaseInstalData"	,"Número de parcelas da compra"),
    "RECURRING_EXPIRY"	 : ("recurringExpiry"	,"Data de expiração do plano recorrente"),
    "RECURRING_FREQUENCY"	 : ("recurringFrequency"	,"Frequência em dias da recorrência (ex.: 31)"),
    "SDK_APP_ID"	 : ("recurringFrequency"	,"Frequência em dias da recorrência (ex.: 31)"),
    "SDK_REF_NUMBER"	 : ("sdkReferenceNumber"	,"Identificador da versão do SDK (fornecido pela EMVCo)"),
    "SDK_TRANS_ID"	 : ("sdkTransID"	,"Transaction ID gerado pelo SDK"),
    "CARDHOLDER_SHIP_ADDR_CITY"	 : ("shipAddrCity"	,"Cidade do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_COUNTRY"	 : ("shipAddrCountry"	,"País do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_LINE1"	 : ("shipAddrLine1"	,"Linha 1 do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_LINE2"	 : ("shipAddrLine2"	,"Linha 2 do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_LINE3"	 : ("shipAddrLine3"	,"Linha 3 do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_POSTAL_CODE"	 : ("shipAddrPostCode"	,"CEP do endereço de entrega"),
    "CARDHOLDER_SHIP_ADDR_STATE"	 : ("shipAddrState"	,"Estado do endereço de entrega"),
    "3DS_REQ_AUTH_IND"	 : ("threeDSRequestorAuthenticationInd"	,"Indica autenticação prévia do portador"),
    "3DS_REQ_AUTH_INFO__threeDSReqAuthMethod"	 : ("threeDSRequestorAuthenticationInfo.threeDSReqAuthMethod"	,"Método utilizado na autenticação prévia"),
    "3DS_REQ_AUTH_INFO__threeDSReqAuthData"	 : ("threeDSRequestorAuthenticationInfo.threeDSReqAuthData"	,"Dados da autenticação prévia"),
    "3DS_REQ_CHALLENGE_IND"	 : ("threeDSRequestorChallengeInd"	,"Indicador de necessidade de desafio"),
    "3DS_REQ_DECOUPLED_MAX_TIME"	 : ("threeDSRequestorDecMaxTime"	,"Tempo máximo de decisão em milissegundos"),
    "3DS_METHOD_COMPLETION_IND"	 : ("threeDSRequestorDecReqInd"	,"Indicador de solicitação de decisão"),
    "REQUESTOR_ID"	 : ("threeDSRequestorID"	,"ID do solicitante 3DS"),
    "REQUESTOR_NAME"	 : ("threeDSRequestorName"	,"Nome do solicitante 3DS"),
    "3DS_SERVER_OPER_ID"	 : ("threeDSServerOperatorID"	,"Identificador do operador do 3DS Server"),
    "3DSS_REF_NUMBER"	 : ("threeDSServerRefNumber"	,"Número de referência do servidor 3DS"),
    "3DS_TRANS_ID"	 : ("threeDSServerTransID"	,"ID da transação do servidor 3DS"),
    "3DS_URL"	 : ("threeDSServerURL"	,"URL do servidor 3DS"),
    "3RI_IND"	 : ("threeRIInd"	,"Indicador de Recurring / Instalments"),
    "TRANSACTION_TYPE"	 : ("transType"	,"Tipo da transação (ex.: 01 = Compra, 03 = Cash Advance)"),
    "CARDHOLDER_IP_ADDRESS"	 : ("appIp"	,"IP da aplicação"),
    "CARDHOLDER_MOBILE_PHONE_NUMBER"	 : ("mobilePhone"	,"Código do país do telefone celular + Número do telefone celular"),
    "CARDHOLDER_HOME_PHONE_NUMBER"	 : ("homePhone"	,"Código do país do telefone residencial + Número do telefone residencial"),
    "CARDHOLDER_WORK_PHONE_NUMBER"	 : ("workPhone"	,"Código do país do telefone comercial + Número do telefone comercial"),
    "CARDHOLDER_INFORMATION_TEXT"	 : ("cardholderInfo.text"	,"Texto exibido ao usuário (mensagem ACS)"),
    "3DS_REQ_DECOUPLED_IND"	 : ("threeDSRequestorDecReqInd"	,"Indicador de solicitação de decisão"),
    "MERCHANT_URL"	 : ("threeDSRequestorURL"	,"URL solicitante"),
    "EMV_PAYMENT_TOKEN_IND"	 : ("payTokenInd"	,"Indica se a transação usa token de pagamento"),
    "EMV_PAYMENT_TOKEN_IND_SOURCE"	 : ("payTokenSource"	,"Origem do token (01=Token Requestor, 02=Issuer Provisioning etc.)"),
    "NOTIFICATION_URL"	 : ("notificationURL"	,"URL para onde o ACS envia notificações (browser/app)"),


    "WHITELIST_STATUS"	 : ("trustListStatus"	,"Status do merchant na trust list"),
    "WHITELIST_STATUS_SOURCE"	 : ("trustListStatusSource"	,"Origem da informação (DS / ACS / Network)"),

    "FLAG_FRAUD" : (None, None),
    "TRANSACTION_STATUS_CODE" : (None, None),
    "TRANSACTION_STATUS" : (None, None),
    "TRANSACTION_STATUS_REASON_CODE" : (None, None),
    "TRANSACTION_STATUS_REASON" : (None, None),
    "TRANSACTION_RESPONSE_CODE": (None, None),
    "CARDHOLDER_IDENTIFIER_BIT_104": (None, None),
    "CARDHOLDER_NAME_BIT_104": (None, None),

    "dataset_flag": (None, "feature criada para divisão do dataset (train, test, oot)"),
}


trained_columns= [

    "ACCT_TYPE",
    "ACQUIRER_BIN",
    "ADDR_MATCH_INDICATOR",
    "CARDHOLDER_BILL_ADDR_COUNTRY",
    "CARDHOLDER_BILL_ADDR_STATE",
    "BROWSER_JAVA_ENABLED",
    "BROWSER_JAVASCRIPT_ENABLED",
    "BROWSER_LANGUAGE",
    "BROWSER_TIME_ZONE",
    "DEVICE_CHANNEL",
    "MERCHANT_CATEGORY_CODE",
    "MERCHANT_COUNTRY",
    "MESSAGE_CATEGORY",
    "AMOUNT",
    "CURRENCY",
    "INSTALMENT_PAYMENT_DATA",
    "CARDHOLDER_SHIP_ADDR_COUNTRY",
    "3DS_REQ_AUTH_IND",
    "3DS_REQ_CHALLENGE_IND",
    "3DS_METHOD_COMPLETION_IND",
    "3DS_SERVER_OPER_ID",
    "TRANSACTION_TYPE",
    "FLAG_FRAUD",

    "dataset_flag",
]


list_normalize_to_string = [
    "TRANSACTION_TYPE",
    "CARDHOLDER_BILL_ADDR_COUNTRY",
    "CARDHOLDER_BILL_ADDR_STATE",
    "CARDHOLDER_SHIP_ADDR_COUNTRY",
    "ACCT_TYPE",
    "CURRENCY",
    "ACQUIRER_BIN",
    "MERCHANT_COUNTRY",
    "MERCHANT_CATEGORY_CODE",
    "3DS_REQ_AUTH_IND",
    "3DS_REQ_CHALLENGE_IND",
    "3DS_SERVER_OPER_ID",
    "3DS_METHOD_COMPLETION_IND",
    "BROWSER_LANGUAGE",
    "BROWSER_TIME_ZONE",
]


list_normalize_to_bool = [
    "BROWSER_JAVA_ENABLED",
    "BROWSER_JAVASCRIPT_ENABLED",
    "ADDR_MATCH_INDICATOR",
    "FLAG_FRAUD",
]

list_normalize_to_double = [
    "DEVICE_CHANNEL",
    "MESSAGE_CATEGORY",
    "AMOUNT",
    "INSTALMENT_PAYMENT_DATA",
]


def normalize_string(x) -> str|None:
    if pd.isna(x):
        return None
    
    x = str(x).strip()

    if x == "":
        return None

    return x


def normalize_bool(x) -> bool|None:
    x = normalize_string(x)

    if x is None:
        return None
    
    x = x.lower()

    if x in {"y", "yes", "s", "sim", "true", "1"}:
        return True

    if x in {"n", "no", "nao", "não", "false", "0"}:
        return False

    return None

def normalization(df):

    for c in list_normalize_to_string:
        df[c] = df[c].apply(normalize_string)

    for c in list_normalize_to_bool:
        df[c] = df[c].apply(normalize_bool)

    for c in list_normalize_to_double:
        df[c] = df[c].apply(pd.to_numeric, errors="coerce").astype("float64")
    
    df["PURCHASE_DATE_AND_TIME"] = pd.to_datetime (
        df["PURCHASE_DATE_AND_TIME"],
        errors="coerce"
    )

    return df

def add_flags(df, end_oot, col_month='PURCHASE_DATE_AND_TIME') -> pd.DataFrame:

    start_oot = end_oot - pd.Timedelta(days=30)
    start_test = start_oot - pd.Timedelta(days=30)

    df["dataset_flag"] = np.select(
        [
            df[col_month] < start_test,
            df[col_month].between(start_test, start_oot, inclusive="left"),
            df[col_month].between(start_oot, end_oot, inclusive="both"),
        ],
        [
            "train",
            "test",
            "oot",
        ],
        default="unknown"
    )

    return df



def expand_json (df : pd.DataFrame) -> pd.DataFrame:
    print("expand_json")
    json_columns = [
            "CARDHOLDER_ACCOUNT_INFORMATION",
            "MERCHANT_RISK_IND",
            "3DS_REQ_AUTH_INFO",
            "3DS_REQ_PRIOR_TRAN_AUTH_INFO",
    ]

    for col in json_columns:
        print(f"proc col: {col}")
        expanded = df[col] .apply(lambda x: {} if pd.isna(x) else json.loads(x) ).apply(pd.Series).add_prefix(f"{col}__")

        df = pd.concat([df.drop(columns=[col]), expanded], axis=1)

    return df


def create_save_summary(df, trained_columns) -> None:

    summary = pd.DataFrame({
        'valores unicos': df.nunique(),
        'nome_pyland' : [di.get(c, [None, None])[0] for c in df.columns],
        'descricao' : [di.get(c, [None, None])[1] for c in df.columns],
        'total nulos': df.isnull().sum(),
        'porcentagem de nulos': df.isnull().mean(),
        'vai para o treinamento': df.columns.isin(trained_columns),
        'tipos': df.dtypes,
        'primeiro valor nao nulo': df.apply(lambda col: col.dropna().iloc[0] if col.notna().any() else None),

    })


    summary.to_csv('./raw_data/summary.csv');



def load_row_data () -> pd.DataFrame:
    print("load row data...")
    files = [
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-01.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-02.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-03.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-04.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-05.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-06.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-07.csv',
        's3://dados-3ds-discover-report/dados-com-fraude/elo-transaction-fraud-marking-2025-08.csv',
    ]

    return pd.concat (
            [pd.read_csv(f) for f in files],
            ignore_index=True
    )

 

def main():

    df = expand_json(load_row_data())

    df = normalization(df)

    df = df[~df["FLAG_FRAUD"].isna()]

    df = add_flags(df, pd.Timestamp("2025-08-17"))

    df.to_parquet('./raw_data/bronze.parquet');

    df[trained_columns].to_parquet('./raw_data/silver.parquet');

    df = create_good_feature (df,"CARDHOLDER_ACCOUNT_IDENTIFIER")

    df[trained_columns + select_new_feat(df) ].to_parquet('./raw_data/gold.parquet');

    create_save_summary(df, trained_columns + select_new_feat(df))
