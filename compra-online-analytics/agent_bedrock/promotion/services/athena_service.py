
# services/athena_service.py
import time
import uuid
import logging
from typing import Dict, Any, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------
# Configuração e constantes
# ----------------------------
AWS_REGION = 'us-east-1'
ATHENA_DATABASE = 'elo_fraud_dev_db'
ATHENA_WORKGROUP = 'elo-fraud-athena-workgroup-dev'
ATHENA_TABLE = 'transaction_results'
S3_OUTPUT = 's3://elo-fraud-athena-results-dev/'
DATE_COLUMN = (
    "COALESCE("
    "try(from_iso8601_timestamp(dt_transaction_datetime)), "
    "try(date_parse(replace(dt_transaction_datetime, 'T', ' '), '%Y-%m-%d %H:%i:%s.%f')), "
    "try(date_parse(dt_transaction_datetime, '%Y-%m-%d %H:%i:%s'))"
    ")"
)
AMOUNT_COLUMN = 'cast(amount as double)'
FRAUD_COLUMN = 'fraud_label'

QUERY_TIMEOUT_MS = 120000 
SLEEP_SECONDS = 0.7

# Cliente Athena
athena = boto3.client("athena", region_name=AWS_REGION)

# ----------------------------
# Query SQL fixa 
# ----------------------------

SQL_QUERY = f"""
    SELECT 
        try_cast(transaction_id AS varchar) AS transaction_id_str,
        {DATE_COLUMN} AS dt, 
        {FRAUD_COLUMN},
        {AMOUNT_COLUMN}
    FROM {ATHENA_DATABASE}.{ATHENA_TABLE}
    WHERE {DATE_COLUMN} >= date_add('day', -30, current_timestamp)
    ORDER BY dt DESC
"""

# ----------------------------
# Serviço: execução e coleta de resultados no Athena
# ----------------------------

def start_query_execution(query: str) -> str:
    """
    Dispara a execução da query no Athena e retorna o QueryExecutionId.
    """
    result_cfg = {
        "OutputLocation": S3_OUTPUT
    }
    kwargs = {
        "QueryString": query,
        "WorkGroup": ATHENA_WORKGROUP,
        "QueryExecutionContext": {"Database": ATHENA_DATABASE},
        "ResultConfiguration": result_cfg,
        "ClientRequestToken": str(uuid.uuid4())
    }
    resp = athena.start_query_execution(**kwargs)
    return resp["QueryExecutionId"]

def wait_for_query(qid: str, timeout_ms: int = QUERY_TIMEOUT_MS) -> Dict[str, Any]:
    """
    Acompanha o status até concluir ou estourar o timeout.
    Retorna o objeto de get_query_execution() quando finaliza.
    """
    start = time.time()
    while True:
        info = athena.get_query_execution(QueryExecutionId=qid)
        state = info["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return info
        if (time.time() - start) * 1000 > timeout_ms:
            raise TimeoutError(f"Athena query timeout: {qid}")
        time.sleep(SLEEP_SECONDS)

def get_results_with_columns(qid: str) -> Dict[str, Any]:
    """
    Retorna todos os resultados mapeados com nomes de colunas.
    Faz paginação até consumir tudo (sem limite de linhas).
    """
    paginator = athena.get_paginator("get_query_results")
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count_total = 0

    for page in paginator.paginate(QueryExecutionId=qid):
        result_set = page.get("ResultSet", {})
        meta = result_set.get("ResultSetMetadata", {})
        colinfo = meta.get("ColumnInfo", [])
        if not columns and colinfo:
            columns = [c.get("Name") for c in colinfo]

        data_rows = result_set.get("Rows", [])

        for r in data_rows:
            cells = [d.get("VarCharValue") if "VarCharValue" in d else None for d in r.get("Data", [])]

            # Pula header (se a primeira linha for exatamente os nomes das colunas)
            if row_count_total == 0 and columns and cells == columns:
                continue

            row_count_total += 1

            # Cria dicionário coluna->valor
            width = max(len(columns), len(cells))
            item = {}
            for i in range(width):
                col_name = columns[i] if i < len(columns) else f"col_{i}"
                val = cells[i] if i < len(cells) else None
                item[col_name] = val
            rows.append(item)

    return {
        "columns": columns,
        "rows": rows,
        "row_count_total": row_count_total
    }

def run_fixed_query() -> Dict[str, Any]:
    """
    Executa a query fixa e retorna seus resultados
    já mapeados com colunas e contagem total.
    Pode levantar TimeoutError, ClientError ou Exception.
    """
    qid = start_query_execution(SQL_QUERY)
    info = wait_for_query(qid, QUERY_TIMEOUT_MS)
    state = info["QueryExecution"]["Status"]["State"]

    if state != "SUCCEEDED":
        err = info["QueryExecution"]["Status"].get("StateChangeReason", "Falha na execução da query.")
        raise RuntimeError(f"Athena falhou: {err}")

    result = get_results_with_columns(qid)
    result["queryExecutionId"] = qid
    return result