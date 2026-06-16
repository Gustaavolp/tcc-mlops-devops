import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from services import athena_service
except ImportError:
    athena_service = None

try:
    from services import mlflow_service
except ImportError:
    mlflow_service = None

try:
    from services import s3_service
except ImportError:
    s3_service = None

from services.bedrock_service import generate_email_payload, get_configured_model_id

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REPORT_S3_URI = os.getenv(
    "STATISTICS_REPORT_S3_URI",
    "s3://elo-fraud-reports-statistics-dev-888577064416",
)

LOOKBACK_HOURS = int(os.getenv("STATISTICS_LOOKBACK_HOURS", "24"))
USE_PARTITIONS = os.getenv("STATISTICS_USE_PARTITIONS", "true").lower() != "false"
PARTITION_DATE_OVERRIDE = os.getenv("STATISTICS_PARTITION_DATE", "").strip()
PARTITION_LOOKBACK_DAYS = int(os.getenv("STATISTICS_PARTITION_LOOKBACK_DAYS", "1"))
TIMEZONE_OFFSET_HOURS = int(os.getenv("STATISTICS_TIMEZONE_OFFSET_HOURS", "-3"))

PARTITION_YEAR_COLUMN = os.getenv("PARTITION_YEAR_COLUMN", "year").strip()
PARTITION_MONTH_COLUMN = os.getenv("PARTITION_MONTH_COLUMN", "month").strip()
PARTITION_DAY_COLUMN = os.getenv("PARTITION_DAY_COLUMN", "day").strip()
PARTITION_HOUR_COLUMN = os.getenv("PARTITION_HOUR_COLUMN", "hour").strip()
PARTITION_LOOKBACK_HOURS = int(os.getenv("STATISTICS_PARTITION_LOOKBACK_HOURS", "24"))

SCORE_COLUMN = os.getenv("SCORE_COLUMN", "score")
SCORE_EXPRESSION = os.getenv("SCORE_EXPRESSION", "").strip()
SCORE_TIMESTAMP_EXPRESSION = os.getenv("SCORE_TIMESTAMP_EXPRESSION", "").strip()
SCORE_TIMESTAMP_COLUMN = os.getenv("SCORE_TIMESTAMP_COLUMN", "").strip()
LATENCY_COLUMN = os.getenv("LATENCY_COLUMN", "").strip()
MODEL_NAME_COLUMN = os.getenv("MODEL_NAME_COLUMN", "").strip()
MODEL_NAME_VALUE = os.getenv("MODEL_NAME_VALUE", "").strip()

SCORE_THRESHOLD_ENV = os.getenv("SCORE_THRESHOLD", "").strip()
THRESHOLD_PARAM_NAME = os.getenv("THRESHOLD_PARAM_NAME", "optimal_threshold")
THRESHOLD_COLUMN = os.getenv("THRESHOLD_COLUMN", "threshold").strip()
SCORE_PERCENTILES = os.getenv("SCORE_PERCENTILES", "0.1,0.25,0.5,0.75,0.9,0.95,0.99")

EXPECTED_PERCENTILES_S3_URI = os.getenv("EXPECTED_PERCENTILES_S3_URI", "").strip()
EXPECTED_DISTRIBUTION_S3_URI = os.getenv("EXPECTED_DISTRIBUTION_S3_URI", "").strip()
DISTRIBUTION_MAX_ABS_DIFF = float(os.getenv("DISTRIBUTION_MAX_ABS_DIFF", "0.05"))
LATENCY_SLA_MS = float(os.getenv("LATENCY_SLA_MS", "200"))

EXCLUDE_DEBUG_EXPERIMENTS = os.getenv("EXCLUDE_DEBUG_EXPERIMENTS", "true").lower() != "false"

ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "elo_fraud_dev_db")
ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "elo-fraud-athena-workgroup-dev")
ATHENA_OUTPUT_S3 = os.getenv("ATHENA_OUTPUT_S3", "s3://aws-athena-query-results-888577064416-us-east-1/")
ATHENA_TABLE = os.getenv("ATHENA_TABLE", "inference_logs")


def _split_s3_uri(uri: str) -> Dict[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError("STATISTICS_REPORT_S3_URI must start with s3://")
    path = uri[5:]
    if not path:
        raise ValueError("STATISTICS_REPORT_S3_URI is missing bucket name")
    parts = path.split("/", 1)
    bucket = parts[0]
    prefix = parts[1].strip("/") if len(parts) > 1 else ""
    return {"bucket": bucket, "prefix": prefix}


def _split_generic_s3_uri(uri: str) -> Tuple[str, str]:
    path = uri[5:]
    parts = path.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


def _parse_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_list_of_floats(raw: str) -> List[float]:
    values = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(float(chunk))
    return values


def _parse_percentile_array(raw: Any) -> Optional[List[float]]:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [float(x) for x in raw]
    text = str(raw).strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    if not text:
        return None
    return [float(v.strip()) for v in text.split(",") if v.strip()]


def _format_percent(value: float, decimals: int = 6) -> str:
    return f"{value * 100:.{decimals}f}%"


def _build_distribution_summary_percent(
    percentiles: Optional[List[float]],
    values: Optional[List[float]],
) -> Optional[str]:
    if not percentiles or not values:
        return None
    targets = [
        (0.5, "P50"),
        (0.9, "P90"),
        (0.95, "P95"),
        (0.99, "P99"),
    ]
    parts = []
    for target, label in targets:
        value = None
        for idx, pct in enumerate(percentiles):
            if abs(pct - target) < 1e-6 and idx < len(values):
                value = values[idx]
                break
        if value is None:
            continue
        parts.append(f"{label} {_format_percent(value)}")
    return " | ".join(parts) if parts else None


def _trim_to_hour(iso_text: Optional[str]) -> Optional[str]:
    if not iso_text:
        return None
    try:
        dt = datetime.fromisoformat(iso_text)
    except ValueError:
        return iso_text
    dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_window_summary(window: Dict[str, Any]) -> Optional[str]:
    mode = window.get("mode")
    if mode == "partition_hourly":
        start = _trim_to_hour(window.get("start"))
        end = _trim_to_hour(window.get("end"))
        if start and end:
            return f"{start} ate {end}"
        return None
    if mode == "partition_daily":
        date = window.get("date")
        return f"data {date}" if date else None
    if mode == "lookback_hours":
        hours = window.get("hours")
        return f"ultimas {hours} horas" if hours is not None else None
    return None


def _resolve_partition_date(now: datetime) -> datetime.date:
    if PARTITION_DATE_OVERRIDE:
        try:
            return datetime.fromisoformat(PARTITION_DATE_OVERRIDE).date()
        except ValueError as exc:
            raise ValueError("STATISTICS_PARTITION_DATE must be YYYY-MM-DD") from exc
    local = now + timedelta(hours=TIMEZONE_OFFSET_HOURS)
    return (local.date() - timedelta(days=PARTITION_LOOKBACK_DAYS))


def _build_partition_filter(now: datetime) -> Tuple[str, Dict[str, Any]]:
    if PARTITION_HOUR_COLUMN:
        local_end = now + timedelta(hours=TIMEZONE_OFFSET_HOURS)
        return _build_hour_partition_filter_for_end(local_end, max(PARTITION_LOOKBACK_HOURS, 1))
    target_date = _resolve_partition_date(now)
    return _build_daily_partition_filter_for_date(target_date)


def _build_daily_partition_filter_for_date(target_date: datetime.date) -> Tuple[str, Dict[str, Any]]:
    clause = (
        f"{PARTITION_YEAR_COLUMN} = {target_date.year} AND "
        f"{PARTITION_MONTH_COLUMN} = {target_date.month} AND "
        f"{PARTITION_DAY_COLUMN} = {target_date.day}"
    )
    return clause, {
        "mode": "partition_daily",
        "date": target_date.isoformat(),
        "lookback_days": PARTITION_LOOKBACK_DAYS,
        "timezone_offset_hours": TIMEZONE_OFFSET_HOURS,
    }


def _build_hour_partition_filter_for_end(local_end: datetime, lookback_hours: int) -> Tuple[str, Dict[str, Any]]:
    partitions = []
    seen = set()
    for offset in range(lookback_hours):
        dt = local_end - timedelta(hours=offset)
        key = (dt.year, dt.month, dt.day, dt.hour)
        if key in seen:
            continue
        seen.add(key)
        partitions.append(
            f"({PARTITION_YEAR_COLUMN} = {dt.year} AND "
            f"{PARTITION_MONTH_COLUMN} = {dt.month} AND "
            f"{PARTITION_DAY_COLUMN} = {dt.day} AND "
            f"{PARTITION_HOUR_COLUMN} = {dt.hour})"
        )
    clause = "(" + " OR ".join(partitions) + ")"
    return clause, {
        "mode": "partition_hourly",
        "start": (local_end - timedelta(hours=lookback_hours)).isoformat(),
        "end": local_end.isoformat(),
        "lookback_hours": lookback_hours,
        "timezone_offset_hours": TIMEZONE_OFFSET_HOURS,
    }


def _build_timestamp_filter() -> Tuple[str, Dict[str, Any]]:
    timestamp_expr = _get_timestamp_expression()
    clause = f"{timestamp_expr} >= date_add('hour', -{LOOKBACK_HOURS}, current_timestamp)"
    return clause, {
        "mode": "lookback_hours",
        "hours": LOOKBACK_HOURS,
    }


def _build_previous_timestamp_filter() -> Tuple[str, Dict[str, Any]]:
    timestamp_expr = _get_timestamp_expression()
    clause = (
        f"{timestamp_expr} >= date_add('hour', -{2 * LOOKBACK_HOURS}, current_timestamp) "
        f"AND {timestamp_expr} < date_add('hour', -{LOOKBACK_HOURS}, current_timestamp)"
    )
    return clause, {
        "mode": "lookback_hours_previous",
        "hours": LOOKBACK_HOURS,
    }


def _get_score_expression() -> str:
    if SCORE_EXPRESSION:
        return SCORE_EXPRESSION
    if SCORE_COLUMN:
        return SCORE_COLUMN
    return ""


def _get_timestamp_expression() -> str:
    if SCORE_TIMESTAMP_EXPRESSION:
        return SCORE_TIMESTAMP_EXPRESSION
    if SCORE_TIMESTAMP_COLUMN:
        return SCORE_TIMESTAMP_COLUMN
    return ""


def _fetch_threshold() -> Tuple[Optional[float], str, Dict[str, Any]]:
    if SCORE_THRESHOLD_ENV:
        return _parse_float(SCORE_THRESHOLD_ENV), "env", {}
    try:
        result = _get_latest_production_run()
        run = result.get("run")
        if not run:
            return None, "missing", result
        aliases = [THRESHOLD_PARAM_NAME, "optimal_threshold", "threshold", "score_threshold"]
        for source_name in ("metrics", "params", "tags"):
            source = run.get(source_name, {})
            for key in aliases:
                if key in source:
                    value = _parse_float(source.get(key))
                    if value is not None:
                        return value, f"mlflow.{source_name}.{key}", result
        return None, "missing", result
    except Exception:
        logger.exception("Failed to fetch threshold from MLflow.")
        return None, "error", {}


def _load_expected_percentiles() -> Optional[Dict[str, Any]]:
    uri = EXPECTED_PERCENTILES_S3_URI or EXPECTED_DISTRIBUTION_S3_URI
    if not uri:
        return None
    bucket, key = _split_generic_s3_uri(uri)
    return _get_json_from_s3(bucket, key)


def _map_expected_percentiles(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw.get("percentiles"), list) and isinstance(raw.get("values"), list):
        return {"percentiles": [float(v) for v in raw["percentiles"]], "values": [float(v) for v in raw["values"]]}
    expected = raw.get("expected_percentiles")
    if isinstance(expected, dict):
        mapped = {float(k): float(v) for k, v in expected.items()}
        keys = sorted(mapped.keys())
        return {"percentiles": keys, "values": [mapped[k] for k in keys]}
    return {}


def _apply_model_filter(clause: str) -> str:
    if MODEL_NAME_COLUMN and MODEL_NAME_VALUE:
        escaped = _escape_sql_literal(MODEL_NAME_VALUE)
        return f"{clause} AND {MODEL_NAME_COLUMN} = '{escaped}'"
    return clause


def _build_filter_clauses(now: datetime) -> Tuple[str, Dict[str, Any], str, Dict[str, Any]]:
    if USE_PARTITIONS and PARTITION_YEAR_COLUMN and PARTITION_MONTH_COLUMN and PARTITION_DAY_COLUMN:
        if PARTITION_HOUR_COLUMN:
            lookback_hours = max(PARTITION_LOOKBACK_HOURS, 1)
            local_end = now + timedelta(hours=TIMEZONE_OFFSET_HOURS)
            current_clause, current_window = _build_hour_partition_filter_for_end(local_end, lookback_hours)
            previous_end = local_end - timedelta(hours=lookback_hours)
            previous_clause, previous_window = _build_hour_partition_filter_for_end(previous_end, lookback_hours)
        else:
            target_date = _resolve_partition_date(now)
            current_clause, current_window = _build_daily_partition_filter_for_date(target_date)
            previous_clause, previous_window = _build_daily_partition_filter_for_date(target_date - timedelta(days=1))
    else:
        current_clause, current_window = _build_timestamp_filter()
        previous_clause, previous_window = _build_previous_timestamp_filter()

    return (
        _apply_model_filter(current_clause),
        current_window,
        _apply_model_filter(previous_clause),
        previous_window,
    )


def _compute_delta_pct(current_value: Optional[float], previous_value: Optional[float]) -> Optional[float]:
    if current_value is None or previous_value is None or previous_value == 0:
        return None
    return ((current_value - previous_value) / previous_value) * 100


def _trend_label(current_value: Optional[float], previous_value: Optional[float], tolerance: float = 1e-12) -> str:
    if current_value is None or previous_value is None:
        return "indisponivel"
    delta = current_value - previous_value
    if abs(delta) <= tolerance:
        return "estavel"
    return "aumentou" if delta > 0 else "diminuiu"


def _build_24h_comparison(
    current_metrics: Dict[str, Any],
    previous_metrics: Dict[str, Any],
    current_window_summary: Optional[str],
    previous_window_summary: Optional[str],
    model_info: Dict[str, Any],
) -> Dict[str, Any]:
    current_scored = current_metrics.get("scored_count")
    previous_scored = previous_metrics.get("scored_count")
    current_score = current_metrics.get("avg_score")
    previous_score = previous_metrics.get("avg_score")
    current_alerts = current_metrics.get("flagged_count")
    previous_alerts = previous_metrics.get("flagged_count")

    experiment = (model_info.get("experiment") or {})
    promotion_ms = experiment.get("effective_update_time")
    promotion_ts = None
    promoted_in_last_48h = False
    if promotion_ms:
        promotion_ts = datetime.fromtimestamp(promotion_ms / 1000, tz=timezone.utc).isoformat()
        promoted_in_last_48h = (datetime.now(timezone.utc) - datetime.fromtimestamp(promotion_ms / 1000, tz=timezone.utc)) <= timedelta(hours=48)

    return {
        "current_window": current_window_summary,
        "previous_window": previous_window_summary,
        "scored_count": {
            "current": current_scored,
            "previous": previous_scored,
            "delta": None if (current_scored is None or previous_scored is None) else current_scored - previous_scored,
            "delta_pct": _compute_delta_pct(
                float(current_scored) if current_scored is not None else None,
                float(previous_scored) if previous_scored is not None else None,
            ),
            "trend": _trend_label(
                float(current_scored) if current_scored is not None else None,
                float(previous_scored) if previous_scored is not None else None,
            ),
        },
        "avg_score": {
            "current": current_score,
            "previous": previous_score,
            "delta": None if (current_score is None or previous_score is None) else current_score - previous_score,
            "delta_pct": _compute_delta_pct(current_score, previous_score),
            "trend": _trend_label(current_score, previous_score),
        },
        "flagged_count": {
            "current": current_alerts,
            "previous": previous_alerts,
            "delta": None if (current_alerts is None or previous_alerts is None) else current_alerts - previous_alerts,
            "delta_pct": _compute_delta_pct(
                float(current_alerts) if current_alerts is not None else None,
                float(previous_alerts) if previous_alerts is not None else None,
            ),
            "trend": _trend_label(
                float(current_alerts) if current_alerts is not None else None,
                float(previous_alerts) if previous_alerts is not None else None,
            ),
        },
        "model_context": {
            "current_model_name": experiment.get("name"),
            "promotion_time": promotion_ts,
            "promoted_in_last_48h": promoted_in_last_48h,
        },
    }


def _build_bedrock_payload(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": report.get("status"),
        "missing": report.get("missing"),
        "window": report.get("window"),
        "window_summary": report.get("window_summary"),
        "model": report.get("model"),
        "metrics": report.get("metrics"),
        "comparison_24h": report.get("comparison_24h"),
        "distribution": report.get("distribution"),
        "distribution_summary_percent": report.get("distribution_summary_percent"),
        "latency": report.get("latency"),
        "threshold": report.get("threshold"),
    }


def _run_query(query: str) -> Dict[str, Any]:
    runner = getattr(athena_service, "run_query", None) if athena_service else None
    if runner:
        return runner(query)
    return _run_query_fallback(query)


def _get_latest_production_run() -> Dict[str, Any]:
    runner = getattr(mlflow_service, "get_latest_production_run", None) if mlflow_service else None
    if not runner:
        logger.warning(
            "services.mlflow_service.get_latest_production_run is missing. "
            "Set SCORE_THRESHOLD to avoid MLflow dependency."
        )
        return {"experiment": None, "run": None}
    return runner(EXCLUDE_DEBUG_EXPERIMENTS)


def _get_json_from_s3(bucket: str, key: str) -> Optional[Dict[str, Any]]:
    getter = getattr(s3_service, "get_json", None) if s3_service else None
    if getter:
        return getter(bucket, key)
    return _get_json_from_s3_fallback(bucket, key)


def _put_json_to_s3(bucket: str, key: str, payload: Dict[str, Any]) -> None:
    writer = getattr(s3_service, "put_json", None) if s3_service else None
    if writer:
        writer(bucket, key, payload)
        return
    _put_json_to_s3_fallback(bucket, key, payload)


def _run_query_fallback(query: str) -> Dict[str, Any]:
    if not ATHENA_DATABASE or not ATHENA_WORKGROUP or not ATHENA_OUTPUT_S3:
        raise ValueError("Athena environment variables are not configured.")
    import time
    import boto3

    athena = boto3.client("athena", region_name=os.getenv("ATHENA_REGION", os.getenv("AWS_REGION", "us-east-1")))
    resp = athena.start_query_execution(
        QueryString=query,
        WorkGroup=ATHENA_WORKGROUP,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_S3},
    )
    query_execution_id = resp["QueryExecutionId"]
    start = time.time()
    timeout_ms = int(os.getenv("ATHENA_QUERY_TIMEOUT_MS", "120000"))
    sleep_seconds = float(os.getenv("ATHENA_POLL_SECONDS", "0.7"))
    while True:
        info = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = info["QueryExecution"]["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            if state != "SUCCEEDED":
                reason = info["QueryExecution"]["Status"].get("StateChangeReason", "Athena query failed.")
                raise RuntimeError(f"Athena failed: {reason}")
            break
        if (time.time() - start) * 1000 > timeout_ms:
            raise TimeoutError(f"Athena query timeout: {query_execution_id}")
        time.sleep(sleep_seconds)

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
    return {"columns": columns, "rows": rows, "row_count_total": row_count_total, "queryExecutionId": query_execution_id}


def _put_json_to_s3_fallback(bucket: str, key: str, payload: Dict[str, Any]) -> None:
    import boto3

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json; charset=utf-8",
    )


def _get_json_from_s3_fallback(bucket: str, key: str) -> Optional[Dict[str, Any]]:
    import boto3

    try:
        s3 = boto3.client("s3")
        resp = s3.get_object(Bucket=bucket, Key=key)
        raw = resp["Body"].read()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        logger.exception("Failed to fetch expected distribution from s3://%s/%s", bucket, key)
        return None


def _run_statistics_query(score_expr: str, where_clause: str, threshold: Optional[float], percentiles: List[float]) -> Dict[str, Any]:
    select_parts = [
        "count(*) AS total_transacoes",
        f"avg({score_expr}) AS score_medio",
    ]
    if THRESHOLD_COLUMN:
        select_parts.append(
            f"sum(CASE WHEN {score_expr} >= {THRESHOLD_COLUMN} THEN 1 ELSE 0 END) AS qtd_fraude_estimada"
        )
        select_parts.append(f"avg({THRESHOLD_COLUMN}) AS threshold_medio")
        select_parts.append(f"min({THRESHOLD_COLUMN}) AS threshold_min")
        select_parts.append(f"max({THRESHOLD_COLUMN}) AS threshold_max")
    elif threshold is not None:
        select_parts.append(
            f"sum(CASE WHEN {score_expr} >= {threshold} THEN 1 ELSE 0 END) AS qtd_fraude_estimada"
        )
    select_parts.append(
        f"approx_percentile({score_expr}, ARRAY[{', '.join(str(p) for p in percentiles)}]) "
        "AS score_distribuicao_percentis"
    )
    if LATENCY_COLUMN:
        select_parts.append(f"avg({LATENCY_COLUMN}) AS latencia_media_ms")
        select_parts.append(f"approx_percentile({LATENCY_COLUMN}, 0.95) AS p95_latencia_ms")

    query = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {ATHENA_DATABASE}.{ATHENA_TABLE} "
        f"WHERE {where_clause}"
    )
    return _run_query(query)


def lambda_handler(event: Optional[Dict[str, Any]], context: Any) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    bedrock_model_id = get_configured_model_id()

    missing = []
    if not ATHENA_DATABASE:
        missing.append("ATHENA_DATABASE")
    if not ATHENA_WORKGROUP:
        missing.append("ATHENA_WORKGROUP")
    if not ATHENA_OUTPUT_S3:
        missing.append("ATHENA_OUTPUT_S3")
    if not ATHENA_TABLE:
        missing.append("ATHENA_TABLE")
    score_expr = _get_score_expression()
    if not score_expr:
        missing.append("SCORE_COLUMN or SCORE_EXPRESSION")
    if not USE_PARTITIONS and not _get_timestamp_expression():
        missing.append("SCORE_TIMESTAMP_EXPRESSION or SCORE_TIMESTAMP_COLUMN")

    report = {
        "report_type": "statistics",
        "generated_at": now.isoformat(),
        "status": "ok",
        "window": {},
        "window_summary": None,
        "previous_window": {},
        "previous_window_summary": None,
        "model": {},
        "metrics": {},
        "previous_metrics": {},
        "comparison_24h": {},
        "distribution": {},
        "latency": {},
        "threshold": {},
        "bedrock_model_id": bedrock_model_id,
        "missing": missing,
    }

    if missing:
        report["status"] = "missing_config"
        email = None
        email_error = None
        try:
            bedrock_payload = _build_bedrock_payload(report)
            email = generate_email_payload(bedrock_payload, model_id=bedrock_model_id)
        except Exception as ex:
            logger.exception("Bedrock generation failed")
            email_error = {"error": str(ex), "error_type": type(ex).__name__}
        report["email"] = email
        report["email_error"] = email_error
        return _write_report(report)

    threshold, threshold_source, model_info = _fetch_threshold()
    report["model"] = {
        "experiment": (model_info.get("experiment") or {}),
        "run": (model_info.get("run") or {}),
    }

    percentiles = _parse_list_of_floats(SCORE_PERCENTILES)
    current_where_clause, current_window, previous_where_clause, previous_window = _build_filter_clauses(now)
    report["window"] = current_window
    report["window_summary"] = _format_window_summary(current_window or {})
    report["previous_window"] = previous_window
    report["previous_window_summary"] = _format_window_summary(previous_window or {})

    result = _run_statistics_query(score_expr, current_where_clause, threshold, percentiles)
    row = result.get("rows", [{}])[0] if result.get("rows") else {}
    previous_result = _run_statistics_query(score_expr, previous_where_clause, threshold, percentiles)
    previous_row = previous_result.get("rows", [{}])[0] if previous_result.get("rows") else {}

    scored_count = _parse_int(row.get("total_transacoes"))
    avg_score = _parse_float(row.get("score_medio"))
    flagged_count = _parse_int(row.get("qtd_fraude_estimada"))
    flagged_rate = None
    if scored_count and flagged_count is not None:
        flagged_rate = flagged_count / scored_count if scored_count else None
    flagged_rate_pct = None
    if flagged_rate is not None:
        flagged_rate_pct = flagged_rate * 100

    threshold_mean = _parse_float(row.get("threshold_medio"))
    threshold_min = _parse_float(row.get("threshold_min"))
    threshold_max = _parse_float(row.get("threshold_max"))
    if threshold is None and threshold_mean is not None:
        threshold = threshold_mean
        threshold_source = "athena.threshold_column_avg"
    report["threshold"] = {
        "value": threshold,
        "source": threshold_source,
        "param_name": THRESHOLD_PARAM_NAME,
        "column": THRESHOLD_COLUMN or None,
        "mode": "column" if THRESHOLD_COLUMN else "static",
        "current_model_value": threshold,
        "current_model_value_source": threshold_source,
        "column_stats": {
            "avg": threshold_mean,
            "min": threshold_min,
            "max": threshold_max,
        },
    }

    percentiles_values = _parse_percentile_array(row.get("score_distribuicao_percentis"))
    distribution_summary_percent = _build_distribution_summary_percent(percentiles, percentiles_values)

    report["metrics"] = {
        "scored_count": scored_count,
        "avg_score": avg_score,
        "flagged_count": flagged_count,
        "flagged_rate": flagged_rate,
        "flagged_rate_pct": flagged_rate_pct,
    }
    previous_scored_count = _parse_int(previous_row.get("total_transacoes"))
    previous_avg_score = _parse_float(previous_row.get("score_medio"))
    previous_flagged_count = _parse_int(previous_row.get("qtd_fraude_estimada"))
    previous_flagged_rate = None
    if previous_scored_count and previous_flagged_count is not None:
        previous_flagged_rate = previous_flagged_count / previous_scored_count if previous_scored_count else None
    previous_flagged_rate_pct = None
    if previous_flagged_rate is not None:
        previous_flagged_rate_pct = previous_flagged_rate * 100
    report["previous_metrics"] = {
        "scored_count": previous_scored_count,
        "avg_score": previous_avg_score,
        "flagged_count": previous_flagged_count,
        "flagged_rate": previous_flagged_rate,
        "flagged_rate_pct": previous_flagged_rate_pct,
    }
    report["comparison_24h"] = _build_24h_comparison(
        report["metrics"],
        report["previous_metrics"],
        report["window_summary"],
        report["previous_window_summary"],
        model_info,
    )

    if LATENCY_COLUMN:
        avg_latency = _parse_float(row.get("latencia_media_ms"))
        p95_latency = _parse_float(row.get("p95_latencia_ms"))
        latency_ok = None
        if avg_latency is not None:
            latency_ok = avg_latency <= LATENCY_SLA_MS
        report["latency"] = {
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "sla_ms": LATENCY_SLA_MS,
            "ok": latency_ok,
        }

    expected_raw = _load_expected_percentiles()
    expected = _map_expected_percentiles(expected_raw or {})
    max_abs_diff = None
    distribution_ok = None
    if expected and percentiles_values:
        diffs = []
        for idx, pct in enumerate(expected.get("percentiles", [])):
            if idx >= len(percentiles_values):
                break
            diffs.append(abs(percentiles_values[idx] - expected["values"][idx]))
        if diffs:
            max_abs_diff = max(diffs)
            distribution_ok = max_abs_diff <= DISTRIBUTION_MAX_ABS_DIFF

    report["distribution"] = {
        "percentiles": percentiles,
        "values": percentiles_values,
        "expected": expected or None,
        "max_abs_diff": max_abs_diff,
        "threshold": DISTRIBUTION_MAX_ABS_DIFF,
        "ok": distribution_ok,
    }
    report["distribution_summary_percent"] = distribution_summary_percent

    email = None
    email_error = None
    try:
        bedrock_payload = _build_bedrock_payload(report)
        email = generate_email_payload(bedrock_payload, model_id=bedrock_model_id)
    except Exception as ex:
        logger.exception("Bedrock generation failed")
        email_error = {"error": str(ex), "error_type": type(ex).__name__}
    report["email"] = email
    report["email_error"] = email_error

    return _write_report(report)


def _write_report(report: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    s3_parts = _split_s3_uri(REPORT_S3_URI)
    date_path = now.strftime("%Y/%m/%d")
    prefix = s3_parts["prefix"]
    key = f"{prefix}/{date_path}/report.json" if prefix else f"{date_path}/report.json"
    _put_json_to_s3(s3_parts["bucket"], key, report)
    report_s3_uri = f"s3://{s3_parts['bucket']}/{key}"
    payload = {"report_s3_uri": report_s3_uri, "status": report.get("status")}
    return {"statusCode": 200, "body": json.dumps(payload)}
