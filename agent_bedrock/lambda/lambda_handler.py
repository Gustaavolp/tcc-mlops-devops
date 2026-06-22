
import json
import logging
import time

from services.athena_service import run_fixed_query
from services.mlflow_service import get_latest_model_info, get_model_metrics
from utils.response_builder import build_bedrock_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Executa a QUERY fixa no Athena e busca informações do último run global no MLflow (via ARN).
    Em seguida, usa o experiment_name retornado para buscar o último run FINISHED daquele experimento.
    Retorna os RESULTADOS para o Bedrock Agent no formato esperado.
    """
    # Log inicial (limitado para não poluir)
    try:
        logger.info("Event: %s", json.dumps(event)[:1000])
    except Exception:
        logger.info("Event: <não serializável ou muito grande>")

    # Metadados Bedrock (ecoamos na resposta)
    action_group = event.get("actionGroup")
    api_path = event.get("apiPath")
    http_method = event.get("httpMethod", "POST")
    session_attributes = event.get("sessionAttributes", {})
    prompt_session_attributes = event.get("promptSessionAttributes", {})

    try:
        # -----------------------------
        # 1) Consulta no Athena
        # -----------------------------
        t0 = time.time()
        athena_result = run_fixed_query()
        t1 = time.time()

        # -----------------------------
        # 2) Consulta no MLflow (último run global)
        # -----------------------------
        latest_global = get_latest_model_info()  # já retorna {"body": {...}}
        t2 = time.time()

        # Log de latência
        logger.info("Timings: athena=%.3fs mlflow_global=%.3fs", t1 - t0, t2 - t1)

        # -----------------------------
        # 3) Consulta no MLflow por experimento
        # -----------------------------
        # Extrai experiment_name do body (se existir)
        exp_name = None
        if isinstance(latest_global, dict) and "body" in latest_global:
            exp_obj = latest_global["body"].get("experiment", {})
            exp_name = exp_obj.get("name")

        if exp_name:
            metrics_by_exp = get_model_metrics(exp_name)  # também em {"body": {...}}
        else:
            metrics_by_exp = {"body": {"error": "Não foi possível determinar o experiment_name a partir do último run global."}}

        t3 = time.time()
        logger.info("Timings: mlflow_by_experiment=%.3fs", t3 - t2)

        # -----------------------------
        # 4) Monta payload com os dois resultados
        # -----------------------------
        payload = {
            "athena": {
                "queryExecutionId": athena_result.get("queryExecutionId"),
                "columns": athena_result.get("columns"),
                "rows": athena_result.get("rows"),
                "row_count_total": athena_result.get("row_count_total")
            },
            "model_latest_global": latest_global,          # {"body": {...}}
            "model_latest_by_experiment": metrics_by_exp   # {"body": {...}}
        }

        return build_bedrock_response(
            action_group, api_path, http_method, 200, payload,
            session_attributes, prompt_session_attributes
        )

    except TimeoutError as te:
        logger.warning("TimeoutError: %s", str(te))
        return build_bedrock_response(
            action_group, api_path, http_method, 504, {"error": str(te)},
            session_attributes, prompt_session_attributes
        )

    except Exception as ex:
        logger.exception("Erro ao executar a query ou buscar dados no MLflow")
        err_payload = {
            "error": str(ex),
            "error_type": type(ex).__name__
        }
        return build_bedrock_response(
            action_group, api_path, http_method, 500, err_payload,
            session_attributes, prompt_session_attributes
        )