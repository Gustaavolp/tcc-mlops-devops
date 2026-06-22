# -----------------------------------------------------------------------------
# Athena Module - Basic Setup
# -----------------------------------------------------------------------------
# Configura Amazon Athena para consultas SQL sobre dados do Process Service
# Recursos: Glue Database, Glue Table, Athena Workgroup, S3 Results Bucket
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# S3 Bucket - Query Results
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "athena_results" {
  bucket        = var.results_bucket_name
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name    = var.results_bucket_name
    Purpose = "Athena Query Results"
  })
}

# -----------------------------------------------------------------------------
# Glue Database
# -----------------------------------------------------------------------------

resource "aws_glue_catalog_database" "main" {
  name        = var.database_name
  description = "Fraud Detection analytics database - ${var.environment}"
}

# -----------------------------------------------------------------------------
# Glue Table - Inference Logs
# -----------------------------------------------------------------------------
# Logs brutos de inferencia para monitoramento e analise
# Atualizado: 2026-02-12 - Schema com 68 colunas do payload real + SerDe mappings
#
# IMPORTANTE: Esta tabela usa Partition Projection para descoberta automatica
# de particoes. O Firehose escreve em inference_logs/YYYY/MM/DD/HH/ e o Athena
# calcula as particoes dinamicamente sem precisar de MSCK REPAIR ou Crawler.
#
# 27 colunas com caracteres especiais (3DS_, -, %) sao mapeadas via
# OpenX JsonSerDe "mapping.<coluna>" parameters.
# -----------------------------------------------------------------------------

resource "aws_glue_catalog_table" "inference_logs" {
  name          = var.inference_logs_table_name
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "json"
    "EXTERNAL"       = "TRUE"

    # Partition Projection - descoberta automatica de particoes
    # Formato Hive-style: year=YYYY/month=MM/day=DD/hour=HH
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = var.partition_projection_year_range
    "projection.year.digits"    = "4"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "projection.hour.type"      = "integer"
    "projection.hour.range"     = "0,23"
    "projection.hour.digits"    = "2"
    "storage.location.template" = "s3://${var.source_bucket_name}/${var.inference_logs_prefix}/year=$${year}/month=$${month}/day=$${day}/hour=$${hour}/"
  }

  storage_descriptor {
    location      = "s3://${var.source_bucket_name}/${var.inference_logs_prefix}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "ignore.malformed.json" = "true"
        "case.insensitive"      = "true"

        # --- 3DS fields (5) - nome JSON comeca com numero ---
        "mapping.tds_trans_id"              = "3DS_TRANS_ID"
        "mapping.tds_req_auth_ind"          = "3DS_REQ_AUTH_IND"
        "mapping.tds_req_challenge_ind"     = "3DS_REQ_CHALLENGE_IND"
        "mapping.tds_server_oper_id"        = "3DS_SERVER_OPER_ID"
        "mapping.tds_method_completion_ind" = "3DS_METHOD_COMPLETION_IND"

        # --- Lag features com "-" (9) ---
        "mapping.nf_feat_lag_amount_n_1"                 = "nf_feat_lag_AMOUNT_n-1"
        "mapping.nf_feat_lag_merchant_country_n_1"       = "nf_feat_lag_MERCHANT_COUNTRY_n-1"
        "mapping.nf_feat_lag_merchant_category_code_n_1" = "nf_feat_lag_MERCHANT_CATEGORY_CODE_n-1"
        "mapping.nf_feat_lag_amount_n_2"                 = "nf_feat_lag_AMOUNT_n-2"
        "mapping.nf_feat_lag_merchant_country_n_2"       = "nf_feat_lag_MERCHANT_COUNTRY_n-2"
        "mapping.nf_feat_lag_merchant_category_code_n_2" = "nf_feat_lag_MERCHANT_CATEGORY_CODE_n-2"
        "mapping.nf_feat_lag_amount_n_3"                 = "nf_feat_lag_AMOUNT_n-3"
        "mapping.nf_feat_lag_merchant_country_n_3"       = "nf_feat_lag_MERCHANT_COUNTRY_n-3"
        "mapping.nf_feat_lag_merchant_category_code_n_3" = "nf_feat_lag_MERCHANT_CATEGORY_CODE_n-3"

        # --- Behaviors com "%" (13) ---
        "mapping.nf_behaviors_pct_merchant_category_code"           = "nf_behaviors_%_MERCHANT_CATEGORY_CODE"
        "mapping.nf_behaviors_pct_nf_enr_user_agent_browser_family" = "nf_behaviors_%_nf_enr_user_agent_browser_family"
        "mapping.nf_behaviors_pct_nf_enr_user_agent_os_family"      = "nf_behaviors_%_nf_enr_user_agent_os_family"
        "mapping.nf_behaviors_pct_nf_enr_user_agent_device_family"  = "nf_behaviors_%_nf_enr_user_agent_device_family"
        "mapping.nf_behaviors_pct_nf_enr_lang"                      = "nf_behaviors_%_nf_enr_lang"
        "mapping.nf_behaviors_pct_nf_enr_period_day"                = "nf_behaviors_%_nf_enr_period_day"
        "mapping.nf_behaviors_pct_nf_enr_day_of_week"               = "nf_behaviors_%_nf_enr_day_of_week"
        "mapping.nf_behaviors_pct_cardholder_bill_addr_city"        = "nf_behaviors_%_CARDHOLDER_BILL_ADDR_CITY"
        "mapping.nf_behaviors_pct_cardholder_bill_addr_country"     = "nf_behaviors_%_CARDHOLDER_BILL_ADDR_COUNTRY"
        "mapping.nf_behaviors_pct_cardholder_ship_addr_city"        = "nf_behaviors_%_CARDHOLDER_SHIP_ADDR_CITY"
        "mapping.nf_behaviors_pct_cardholder_ship_addr_country"     = "nf_behaviors_%_CARDHOLDER_SHIP_ADDR_COUNTRY"
        "mapping.nf_behaviors_pct_merchant_id"                      = "nf_behaviors_%_MERCHANT_ID"
        "mapping.nf_behaviors_pct_currency"                         = "nf_behaviors_%_CURRENCY"
      }
    }

    # =========================================================================
    # Identificacao e transacao (8)
    # =========================================================================
    columns {
      name    = "tds_trans_id"
      type    = "string"
      comment = "Mapeado de 3DS_TRANS_ID"
    }
    columns {
      name = "cardholder_account_identifier"
      type = "string"
    }
    columns {
      name = "purchase_date_and_time"
      type = "string"
    }
    columns {
      name = "device_channel"
      type = "double"
    }
    columns {
      name = "message_category"
      type = "double"
    }
    columns {
      name = "amount"
      type = "double"
    }
    columns {
      name = "instalment_payment_data"
      type = "double"
    }
    columns {
      name = "transaction_type"
      type = "string"
    }

    # =========================================================================
    # Endereco e cartao (4)
    # =========================================================================
    columns {
      name = "cardholder_bill_addr_country"
      type = "string"
    }
    columns {
      name = "cardholder_bill_addr_state"
      type = "string"
    }
    columns {
      name = "cardholder_ship_addr_country"
      type = "string"
    }
    columns {
      name = "acct_type"
      type = "string"
    }

    # =========================================================================
    # Merchant e financeiro (4)
    # =========================================================================
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "acquirer_bin"
      type = "string"
    }
    columns {
      name = "merchant_country"
      type = "string"
    }
    columns {
      name = "merchant_category_code"
      type = "string"
    }

    # =========================================================================
    # 3DS Protocol (4) - todos com mapping
    # =========================================================================
    columns {
      name    = "tds_req_auth_ind"
      type    = "string"
      comment = "Mapeado de 3DS_REQ_AUTH_IND"
    }
    columns {
      name    = "tds_req_challenge_ind"
      type    = "string"
      comment = "Mapeado de 3DS_REQ_CHALLENGE_IND"
    }
    columns {
      name    = "tds_server_oper_id"
      type    = "string"
      comment = "Mapeado de 3DS_SERVER_OPER_ID"
    }
    columns {
      name    = "tds_method_completion_ind"
      type    = "string"
      comment = "Mapeado de 3DS_METHOD_COMPLETION_IND"
    }

    # =========================================================================
    # Browser e device (5)
    # =========================================================================
    columns {
      name = "browser_language"
      type = "string"
    }
    columns {
      name = "browser_time_zone"
      type = "string"
    }
    columns {
      name = "browser_java_enabled"
      type = "boolean"
    }
    columns {
      name = "browser_javascript_enabled"
      type = "boolean"
    }
    columns {
      name = "dataset_flag"
      type = "string"
    }

    # =========================================================================
    # Indicadores (2)
    # =========================================================================
    columns {
      name = "addr_match_indicator"
      type = "boolean"
    }
    columns {
      name = "flag_fraud"
      type = "boolean"
    }
    columns {
      name    = "score"
      type    = "double"
      comment = "Probabilidade de fraude do modelo XGBoost"
    }
    columns {
      name    = "threshold"
      type    = "double"
      comment = "Threshold otimo usado na classificacao (vem do MLflow)"
    }

    # =========================================================================
    # Features NF - enrichment (6)
    # =========================================================================
    columns {
      name = "nf_enr_user_agent_browser_family"
      type = "string"
    }
    columns {
      name = "nf_enr_user_agent_os_family"
      type = "string"
    }
    columns {
      name = "nf_enr_lang"
      type = "string"
    }
    columns {
      name = "nf_enr_instalment_payment_data"
      type = "double"
    }
    columns {
      name = "nf_enr_period_day"
      type = "string"
    }
    columns {
      name = "nf_enr_day_of_week"
      type = "string"
    }

    # =========================================================================
    # Features NF - lag (10) - todos com mapping por "-"
    # =========================================================================
    columns {
      name = "nf_seconds_since_last_tx"
      type = "double"
    }
    columns {
      name    = "nf_feat_lag_amount_n_1"
      type    = "double"
      comment = "Mapeado de nf_feat_lag_AMOUNT_n-1"
    }
    columns {
      name    = "nf_feat_lag_merchant_country_n_1"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_COUNTRY_n-1"
    }
    columns {
      name    = "nf_feat_lag_merchant_category_code_n_1"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_CATEGORY_CODE_n-1"
    }
    columns {
      name    = "nf_feat_lag_amount_n_2"
      type    = "double"
      comment = "Mapeado de nf_feat_lag_AMOUNT_n-2"
    }
    columns {
      name    = "nf_feat_lag_merchant_country_n_2"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_COUNTRY_n-2"
    }
    columns {
      name    = "nf_feat_lag_merchant_category_code_n_2"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_CATEGORY_CODE_n-2"
    }
    columns {
      name    = "nf_feat_lag_amount_n_3"
      type    = "double"
      comment = "Mapeado de nf_feat_lag_AMOUNT_n-3"
    }
    columns {
      name    = "nf_feat_lag_merchant_country_n_3"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_COUNTRY_n-3"
    }
    columns {
      name    = "nf_feat_lag_merchant_category_code_n_3"
      type    = "string"
      comment = "Mapeado de nf_feat_lag_MERCHANT_CATEGORY_CODE_n-3"
    }

    # =========================================================================
    # Features NF - behaviors (13) - todos com mapping por "%"
    # =========================================================================
    columns {
      name    = "nf_behaviors_pct_merchant_category_code"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_MERCHANT_CATEGORY_CODE"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_user_agent_browser_family"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_user_agent_browser_family"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_user_agent_os_family"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_user_agent_os_family"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_user_agent_device_family"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_user_agent_device_family"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_lang"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_lang"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_period_day"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_period_day"
    }
    columns {
      name    = "nf_behaviors_pct_nf_enr_day_of_week"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_nf_enr_day_of_week"
    }
    columns {
      name    = "nf_behaviors_pct_cardholder_bill_addr_city"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_CARDHOLDER_BILL_ADDR_CITY"
    }
    columns {
      name    = "nf_behaviors_pct_cardholder_bill_addr_country"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_CARDHOLDER_BILL_ADDR_COUNTRY"
    }
    columns {
      name    = "nf_behaviors_pct_cardholder_ship_addr_city"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_CARDHOLDER_SHIP_ADDR_CITY"
    }
    columns {
      name    = "nf_behaviors_pct_cardholder_ship_addr_country"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_CARDHOLDER_SHIP_ADDR_COUNTRY"
    }
    columns {
      name    = "nf_behaviors_pct_merchant_id"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_MERCHANT_ID"
    }
    columns {
      name    = "nf_behaviors_pct_currency"
      type    = "double"
      comment = "Mapeado de nf_behaviors_%_CURRENCY"
    }

    # =========================================================================
    # Features NF - amount statistics (12)
    # =========================================================================
    columns {
      name = "nf_amount_mean_last_15"
      type = "double"
    }
    columns {
      name = "nf_amount_median_last_15"
      type = "double"
    }
    columns {
      name = "nf_amount_std_last_15"
      type = "double"
    }
    columns {
      name = "nf_amount_zscore_15"
      type = "double"
    }
    columns {
      name = "nf_amount_mean_last_10"
      type = "double"
    }
    columns {
      name = "nf_amount_median_last_10"
      type = "double"
    }
    columns {
      name = "nf_amount_std_last_10"
      type = "double"
    }
    columns {
      name = "nf_amount_zscore_10"
      type = "double"
    }
    columns {
      name = "nf_amount_mean_last_5"
      type = "double"
    }
    columns {
      name = "nf_amount_median_last_5"
      type = "double"
    }
    columns {
      name = "nf_amount_std_last_5"
      type = "double"
    }
    columns {
      name = "nf_amount_zscore_5"
      type = "double"
    }
  }

  # Particoes: year, month, day, hour
  partition_keys {
    name = "year"
    type = "int"
  }
  partition_keys {
    name = "month"
    type = "int"
  }
  partition_keys {
    name = "day"
    type = "int"
  }
  partition_keys {
    name = "hour"
    type = "int"
  }
}

# -----------------------------------------------------------------------------
# Athena Workgroup
# -----------------------------------------------------------------------------

resource "aws_athena_workgroup" "main" {
  name  = var.workgroup_name
  state = "ENABLED"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.id}/results/"
    }

    bytes_scanned_cutoff_per_query     = var.bytes_scanned_limit
    publish_cloudwatch_metrics_enabled = true
  }

  tags = merge(var.tags, {
    Name = var.workgroup_name
  })
}
