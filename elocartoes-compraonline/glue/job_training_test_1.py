import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.conf import SparkConf
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, BooleanType
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# --- 1. CONFIGURAÇÃO ---
conf = SparkConf()
conf.set("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
conf.set("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

sc = SparkContext(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'INPUT_PATH', 'OUTPUT_PATH'])
job.init(args['JOB_NAME'], args)

INPUT_PATH = args['INPUT_PATH']
OUTPUT_PATH = args['OUTPUT_PATH']

# --- 2. SCHEMA DEFINIDO ---
schema_silver_training = StructType([
    StructField("3DS_TRANS_ID", StringType(), True),
    StructField("CARDHOLDER_ACCOUNT_IDENTIFIER", StringType(), True),
    StructField("PURCHASE_DATE_AND_TIME", StringType(), True),

    # --- Features Numéricas ---
    StructField("DEVICE_CHANNEL", DoubleType(), True),
    StructField("MESSAGE_CATEGORY", DoubleType(), True),
    StructField("AMOUNT", DoubleType(), True),
    StructField("INSTALMENT_PAYMENT_DATA", DoubleType(), True),

    # --- Features Categóricas ---
    StructField("TRANSACTION_TYPE", StringType(), True),
    StructField("ACCT_TYPE", StringType(), True),
    StructField("CURRENCY", StringType(), True),
    StructField("ACQUIRER_BIN", StringType(), True),
    StructField("MERCHANT_COUNTRY", StringType(), True),
    StructField("MERCHANT_CATEGORY_CODE", StringType(), True),

    # --- Endereço ---
    StructField("CARDHOLDER_BILL_ADDR_COUNTRY", StringType(), True),
    StructField("CARDHOLDER_BILL_ADDR_STATE", StringType(), True),
    StructField("CARDHOLDER_SHIP_ADDR_COUNTRY", StringType(), True),

    # --- 3DS & Auth ---
    StructField("3DS_REQ_AUTH_IND", StringType(), True),
    StructField("3DS_REQ_CHALLENGE_IND", StringType(), True),
    StructField("3DS_SERVER_OPER_ID", StringType(), True),
    StructField("3DS_METHOD_COMPLETION_IND", StringType(), True),

    # --- Browser & Ambiente ---
    StructField("BROWSER_LANGUAGE", StringType(), True),
    StructField("BROWSER_TIME_ZONE", StringType(), True),
    StructField("BROWSER_JAVA_ENABLED", BooleanType(), True),
    StructField("BROWSER_JAVASCRIPT_ENABLED", BooleanType(), True),
    StructField("ADDR_MATCH_INDICATOR", BooleanType(), True),

    # --- Targets e Flags ---
    StructField("FLAG_FRAUD", BooleanType(), True),
    StructField("dataset_flag", StringType(), True),

    # --- NOVAS FEATURES ---
    StructField("nf_enr_user_agent_browser_family", StringType(), True),
    StructField("nf_enr_user_agent_os_family", StringType(), True),
    StructField("nf_enr_lang", StringType(), True),
    StructField("nf_enr_instalment_payment_data", DoubleType(), True),
    StructField("nf_enr_period_day", StringType(), True),
    StructField("nf_enr_day_of_week", StringType(), True),
    StructField("nf_seconds_since_last_tx", DoubleType(), True),
    StructField("nf_feat_lag_AMOUNT_n-1", DoubleType(), True),
    StructField("nf_feat_lag_MERCHANT_COUNTRY_n-1", StringType(), True),
    StructField("nf_feat_lag_MERCHANT_CATEGORY_CODE_n-1", StringType(), True),
    StructField("nf_feat_lag_AMOUNT_n-2", DoubleType(), True),
    StructField("nf_feat_lag_MERCHANT_COUNTRY_n-2", StringType(), True),
    StructField("nf_feat_lag_MERCHANT_CATEGORY_CODE_n-2", StringType(), True),
    StructField("nf_feat_lag_AMOUNT_n-3", DoubleType(), True),
    StructField("nf_feat_lag_MERCHANT_COUNTRY_n-3", StringType(), True),
    StructField("nf_feat_lag_MERCHANT_CATEGORY_CODE_n-3", StringType(), True),
    StructField("nf_behaviors_%_MERCHANT_CATEGORY_CODE", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_user_agent_browser_family", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_user_agent_os_family", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_user_agent_device_family", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_lang", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_period_day", DoubleType(), True),
    StructField("nf_behaviors_%_nf_enr_day_of_week", DoubleType(), True),
    StructField("nf_behaviors_%_CARDHOLDER_BILL_ADDR_CITY", DoubleType(), True),
    StructField("nf_behaviors_%_CARDHOLDER_BILL_ADDR_COUNTRY", DoubleType(), True),
    StructField("nf_behaviors_%_CARDHOLDER_SHIP_ADDR_CITY", DoubleType(), True),
    StructField("nf_behaviors_%_CARDHOLDER_SHIP_ADDR_COUNTRY", DoubleType(), True),
    StructField("nf_behaviors_%_MERCHANT_ID", DoubleType(), True),
    StructField("nf_behaviors_%_CURRENCY", DoubleType(), True),
    StructField("nf_amount_mean_last_15", DoubleType(), True),
    StructField("nf_amount_median_last_15", DoubleType(), True),
    StructField("nf_amount_std_last_15", DoubleType(), True),
    StructField("nf_amount_zscore_15", DoubleType(), True),
    StructField("nf_amount_mean_last_10", DoubleType(), True),
    StructField("nf_amount_median_last_10", DoubleType(), True),
    StructField("nf_amount_std_last_10", DoubleType(), True),
    StructField("nf_amount_zscore_10", DoubleType(), True),
    StructField("nf_amount_mean_last_5", DoubleType(), True),
    StructField("nf_amount_median_last_5", DoubleType(), True),
    StructField("nf_amount_std_last_5", DoubleType(), True),
    StructField("nf_amount_zscore_5", DoubleType(), True)
])

try:
    # --- 3. LEITURA ---
    print(f"Lendo dados brutos como TEXTO de: {INPUT_PATH}")

    df_text = spark.read \
        .option("recursiveFileLookup", "true") \
        .text(INPUT_PATH)

    if df_text.isEmpty():
        print("Nenhum dado encontrado.")
        sys.exit(0)

    df_fixed_strings = df_text.select(
        F.explode(
            F.split(
                F.regexp_replace(F.col("value"), "\\}\\{", "\\}\\|\\{"),
                "\\|"
            )
        ).alias("json_string")
    )

    print("Aplicando Schema estruturado...")
    df_parsed = df_fixed_strings.select(
        F.from_json(F.col("json_string"), schema_silver_training).alias("data")
    ).select("data.*")

    df_raw = df_parsed.filter(F.col("3DS_TRANS_ID").isNotNull()) \
                      .withColumn("3DS_TRANS_ID", F.trim(F.col("3DS_TRANS_ID")))

    print(f"Total de registros recuperados e válidos: {df_raw.count()}")

    # --- 4. LIMPEZA E DEDUPLICAÇÃO ---
    print("Iniciando limpeza e deduplicação...")

    df_clean = df_raw.withColumn("3DS_TRANS_ID", F.trim(F.col("3DS_TRANS_ID")))

    window_spec = Window.partitionBy("3DS_TRANS_ID").orderBy(
        F.when(F.col("nf_enr_user_agent_browser_family").isNotNull(), 1).otherwise(0).desc(),
        F.col("PURCHASE_DATE_AND_TIME").desc()
    )

    df_dedup = df_clean.withColumn("rank", F.row_number().over(window_spec)) \
                      .filter(F.col("rank") == 1) \
                      .drop("rank")

    # --- 5. MERGE COM CONTROLE DE CONTAGEM ---
    print(f"Executando MERGE na tabela Delta: {OUTPUT_PATH}")

    if DeltaTable.isDeltaTable(spark, OUTPUT_PATH):
        deltaTable = DeltaTable.forPath(spark, OUTPUT_PATH)

        count_before = deltaTable.toDF().count()
        print(f"Total na Delta ANTES do Merge: {count_before}")

        deltaTable.alias("target").merge(
            source = df_dedup.alias("source"),
            condition = "target.3DS_TRANS_ID = source.3DS_TRANS_ID"
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).execute()

        count_after = spark.read.format("delta").load(OUTPUT_PATH).count()
        print(f"Total na Delta DEPOIS do Merge: {count_after}")
        print(f"NOVOS REGISTROS INSERIDOS: {count_after - count_before}")

    else:
        print("Tabela Delta não encontrada. Criando nova tabela...")
        df_dedup.write \
            .format("delta") \
            .mode("overwrite") \
            .save(OUTPUT_PATH)
        print("Tabela criada e carregada inicialmente.")

    # --- 6. OTIMIZAÇÃO ---
    try:
        spark.sql(f"OPTIMIZE delta.`{OUTPUT_PATH}` ZORDER BY (PURCHASE_DATE_AND_TIME)")
        print("Otimização Z-ORDER concluída.")
    except Exception as e:
        print(f"Aviso na otimização: {e}")

except Exception as e:
    print(f"ERRO CRÍTICO: {str(e)}")
    sys.exit(1)

job.commit()
