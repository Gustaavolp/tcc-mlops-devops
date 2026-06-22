import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from services.bedrock_service import generate_email_payload, get_configured_model_id
from services.mlflow_service import collect_recent_promotions, extract_dataset_info
from services.s3_service import put_json
from utils.response_builder import build_bedrock_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REPORT_S3_URI = os.getenv(
    "PROMOTION_REPORT_S3_URI",
    "s3://elo-fraud-reports-promotion-dev-888577064416",
)
MLFLOW_APP_ARN = os.getenv(
    "MLFLOW_APP_ARN",
    "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ",
)
EXCLUDE_DEBUG = os.getenv("EXCLUDE_DEBUG_EXPERIMENTS", "true").lower() != "false"
PROMOTION_LOOKBACK_HOURS = int(os.getenv("PROMOTION_LOOKBACK_HOURS", "240"))
ALLOW_METRIC_FALLBACK = os.getenv("ALLOW_METRIC_FALLBACK", "false").lower() == "true"
FALLBACK_METRIC = os.getenv("FALLBACK_METRIC", "best_cv_score")


def _split_s3_uri(uri: str) -> Dict[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError("PROMOTION_REPORT_S3_URI must start with s3://")
    path = uri[5:]
    if not path:
        raise ValueError("PROMOTION_REPORT_S3_URI is missing bucket name")
    parts = path.split("/", 1)
    bucket = parts[0]
    prefix = parts[1].strip("/") if len(parts) > 1 else ""
    return {"bucket": bucket, "prefix": prefix}


def _ms_to_iso(ms: Optional[int]) -> Optional[str]:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_comparison(current_run: Optional[Dict[str, Any]], previous_run: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    def _get_metric(run: Optional[Dict[str, Any]], metric_name: str) -> Optional[float]:
        if not run:
            return None
        return _safe_float(run.get("metrics", {}).get(metric_name))

    current_f1 = _get_metric(current_run, "f1_oot")
    previous_f1 = _get_metric(previous_run, "f1_oot")

    metric_name = "f1_oot"
    metric_current = current_f1
    metric_previous = previous_f1

    if ALLOW_METRIC_FALLBACK and (metric_current is None or metric_previous is None):
        fallback_current = _get_metric(current_run, FALLBACK_METRIC)
        fallback_previous = _get_metric(previous_run, FALLBACK_METRIC)
        if fallback_current is not None and fallback_previous is not None:
            metric_name = FALLBACK_METRIC
            metric_current = fallback_current
            metric_previous = fallback_previous

    metric_delta = None
    if metric_current is not None and metric_previous is not None:
        metric_delta = metric_current - metric_previous

    reason = None
    if metric_current is not None and metric_previous is not None:
        if metric_current > metric_previous:
            reason = f"{metric_name} improved from {metric_previous:.4f} to {metric_current:.4f}"
        elif metric_current < metric_previous:
            reason = f"{metric_name} decreased from {metric_previous:.4f} to {metric_current:.4f}"
        else:
            reason = f"{metric_name} unchanged at {metric_current:.4f}"

    return {
        "f1_oot_current": current_f1,
        "f1_oot_previous": previous_f1,
        "f1_oot_delta": None if (current_f1 is None or previous_f1 is None) else current_f1 - previous_f1,
        "metric_name": metric_name,
        "metric_current": metric_current,
        "metric_previous": metric_previous,
        "metric_delta": metric_delta,
        "metric_is_fallback": metric_name != "f1_oot",
        "reason": reason,
    }


def _build_bedrock_payload(promotion: Dict[str, Any]) -> Dict[str, Any]:
    exp = promotion.get("experiment", {})
    prev_exp = promotion.get("previous_experiment")
    current_run = promotion.get("current_run")
    previous_run = promotion.get("previous_run")
    dataset_info = {}
    if current_run:
        dataset_info = extract_dataset_info(current_run.get("params", {}), current_run.get("tags", {}))
    comparison = _build_comparison(current_run, previous_run)

    return {
        "model_name": exp.get("name"),
        "experiment_id": exp.get("experiment_id"),
        "promoted_at": _ms_to_iso(exp.get("effective_update_time")),
        "current_run": {
            "run_id": current_run.get("run_id") if current_run else None,
            "start_time": _ms_to_iso(current_run.get("start_time")) if current_run else None,
            "metrics": current_run.get("metrics") if current_run else {},
            "params": current_run.get("params") if current_run else {},
            "tags": current_run.get("tags") if current_run else {},
        },
        "previous_model": {
            "name": prev_exp.get("name") if prev_exp else None,
            "experiment_id": prev_exp.get("experiment_id") if prev_exp else None,
            "run_id": previous_run.get("run_id") if previous_run else None,
            "metrics": previous_run.get("metrics") if previous_run else {},
        },
        "dataset_info": dataset_info,
        "comparison": comparison,
    }


def lambda_handler(event, context):
    try:
        logger.info("Event: %s", json.dumps(event)[:1000])
    except Exception:
        logger.info("Event: <unserializable or too large>")

    action_group = event.get("actionGroup")
    api_path = event.get("apiPath")
    http_method = event.get("httpMethod", "POST")
    session_attributes = event.get("sessionAttributes", {})
    prompt_session_attributes = event.get("promptSessionAttributes", {})

    now = datetime.now(timezone.utc)
    window_end = now
    window_start = now - timedelta(hours=PROMOTION_LOOKBACK_HOURS)
    since_ms = int(window_start.timestamp() * 1000)
    bedrock_model_id = get_configured_model_id()

    try:
        promotions = collect_recent_promotions(since_ms=since_ms, exclude_debug=EXCLUDE_DEBUG)
        report_items = []

        for promotion in promotions:
            bedrock_payload = _build_bedrock_payload(promotion)
            email = None
            email_error = None
            try:
                email = generate_email_payload(bedrock_payload, model_id=bedrock_model_id)
            except Exception as ex:
                logger.exception("Bedrock generation failed")
                email_error = {"error": str(ex), "error_type": type(ex).__name__}

            report_items.append(
                {
                    "experiment": promotion.get("experiment"),
                    "current_run": promotion.get("current_run"),
                    "previous_experiment": promotion.get("previous_experiment"),
                    "previous_run": promotion.get("previous_run"),
                    "comparison": bedrock_payload.get("comparison"),
                    "dataset_info": bedrock_payload.get("dataset_info"),
                    "email": email,
                    "email_error": email_error,
                }
            )

        report = {
            "report_type": "promotion",
            "generated_at": now.isoformat(),
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "mlflow_app_arn": MLFLOW_APP_ARN,
            "bedrock_model_id": bedrock_model_id,
            "promotion_count": len(report_items),
            "promotions": report_items,
        }

        s3_parts = _split_s3_uri(REPORT_S3_URI)
        date_path = now.strftime("%Y/%m/%d")
        prefix = s3_parts["prefix"]
        key = f"{prefix}/{date_path}/report.json" if prefix else f"{date_path}/report.json"
        put_json(s3_parts["bucket"], key, report)
        report_s3_uri = f"s3://{s3_parts['bucket']}/{key}"

        payload = {
            "report_s3_uri": report_s3_uri,
            "promotion_count": len(report_items),
        }

        if action_group or api_path:
            return build_bedrock_response(
                action_group,
                api_path,
                http_method,
                200,
                payload,
                session_attributes,
                prompt_session_attributes,
            )
        return {"statusCode": 200, "body": json.dumps(payload)}

    except Exception as ex:
        logger.exception("Failed to generate promotion report")
        err_payload = {"error": str(ex), "error_type": type(ex).__name__}
        if action_group or api_path:
            return build_bedrock_response(
                action_group,
                api_path,
                http_method,
                500,
                err_payload,
                session_attributes,
                prompt_session_attributes,
            )
        return {"statusCode": 500, "body": json.dumps(err_payload)}
