import logging
import os
import time
from typing import Any, Dict, List

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ATHENA_REGION = os.getenv("ATHENA_REGION", os.getenv("AWS_REGION", "us-east-1"))
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "elo_fraud_dev_db")
ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "elo-fraud-athena-workgroup-dev")
ATHENA_OUTPUT = os.getenv("ATHENA_OUTPUT_S3", "s3://aws-athena-query-results-888577064416-us-east-1/")

QUERY_TIMEOUT_MS = int(os.getenv("ATHENA_QUERY_TIMEOUT_MS", "120000"))
SLEEP_SECONDS = float(os.getenv("ATHENA_POLL_SECONDS", "0.7"))

athena = boto3.client("athena", region_name=ATHENA_REGION)


def start_query_execution(query: str) -> str:
    if not ATHENA_DATABASE or not ATHENA_WORKGROUP or not ATHENA_OUTPUT:
        raise ValueError("Athena environment variables are not configured.")
    resp = athena.start_query_execution(
        QueryString=query,
        WorkGroup=ATHENA_WORKGROUP,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
    )
    return resp["QueryExecutionId"]


def wait_for_query(query_execution_id: str, timeout_ms: int = QUERY_TIMEOUT_MS) -> Dict[str, Any]:
    start = time.time()
    while True:
        info = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = info["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return info
        if (time.time() - start) * 1000 > timeout_ms:
            raise TimeoutError(f"Athena query timeout: {query_execution_id}")
        time.sleep(SLEEP_SECONDS)


def get_results_with_columns(query_execution_id: str) -> Dict[str, Any]:
    paginator = athena.get_paginator("get_query_results")
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count_total = 0

    for page in paginator.paginate(QueryExecutionId=query_execution_id):
        result_set = page.get("ResultSet", {})
        meta = result_set.get("ResultSetMetadata", {})
        colinfo = meta.get("ColumnInfo", [])
        if not columns and colinfo:
            columns = [c.get("Name") for c in colinfo]

        data_rows = result_set.get("Rows", [])
        for r in data_rows:
            cells = [d.get("VarCharValue") if "VarCharValue" in d else None for d in r.get("Data", [])]
            if row_count_total == 0 and columns and cells == columns:
                continue
            row_count_total += 1
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
        "row_count_total": row_count_total,
    }


def run_query(query: str) -> Dict[str, Any]:
    query_execution_id = start_query_execution(query)
    info = wait_for_query(query_execution_id, QUERY_TIMEOUT_MS)
    state = info["QueryExecution"]["Status"]["State"]
    if state != "SUCCEEDED":
        err = info["QueryExecution"]["Status"].get("StateChangeReason", "Athena query failed.")
        raise RuntimeError(f"Athena failed: {err}")
    result = get_results_with_columns(query_execution_id)
    result["queryExecutionId"] = query_execution_id
    return result
