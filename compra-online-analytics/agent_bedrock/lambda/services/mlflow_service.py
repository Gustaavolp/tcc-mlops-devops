
import mlflow
from mlflow import MlflowClient
from mlflow.entities import ViewType

# MLflow Tracking (gerenciado no SageMaker via ARN)
MLFLOW_TRACKING_ARN = "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ"


def _extract_run_payload(runs_df, client: MlflowClient) -> dict:
    """
    Extrai as métricas PEDIDAS (accuracy, precision, recall, f1 a partir de f1_score, auc),
    e também run_id e start_time, no formato:
      {"body": {"experiment": {"id", "name"}, "metrics": {...}}}
    """
    if runs_df is None or runs_df.empty:
        return {"body": {"error": "No runs found"}}

    r = runs_df.iloc[0]

    # Experiment info
    exp_id = r.get("experiment_id")
    exp = client.get_experiment(exp_id) if exp_id else None
    experiment = {"id": exp_id, "name": getattr(exp, "name", None)}

    # Métricas específicas (com tolerância a ausências)
    metrics = {
        "best_cv_score": r.get("metrics.best_cv_score"),
        "ppr_teste": r.get("metrics.ppr_teste"),
        "ppr_oot": r.get("metrics.ppr_oot"),
        "f1_teste": r.get("metrics.f1_teste"),
        "f1_oot": r.get("metrics.f1_oot"),
        "training_score": r.get("metrics.training_score"),
        "training_f1_score": r.get("metrics.training_f1_score"),
        "training_log_loss": r.get("metrics.training_log_loss"),
        "training_accuracy_score": r.get("metrics.training_accuracy_score"),
        "training_precision_score": r.get("metrics.training_precision_score"),
        "training_recall_score": r.get("metrics.training_recall_score"),
        "training_roc_auc": r.get("metrics.training_roc_auc"),
        "optimal_threshold": r.get("metrics.optimal_threshold"),
        "run_id": r.get("run_id"),
        "start_time": r.get("attributes.start_time")
    }

    return {"body": {"experiment": experiment, "metrics": metrics}}


def get_latest_model_info() -> dict:
    """
    Conecta ao MLflow (via ARN) e retorna o último run FINISHED entre TODOS os experimentos ativos.
    Se não houver FINISHED, faz fallback para o realmente último (sem filtro).

    Retorna:
      {"body": {"experiment": {"id","name"}, "metrics": {...}}}
    """
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_ARN)  # requer sagemaker-mlflow quando ARN é usado
        client = MlflowClient()

        # Lista experimentos ativos (usa API de alto nível; fallback no client)
        try:
            exps = mlflow.list_experiments(view_type=ViewType.ACTIVE_ONLY)
        except Exception:
            exps = client.search_experiments(view_type=ViewType.ACTIVE_ONLY)

        exp_ids = [e.experiment_id for e in exps]
        if not exp_ids:
            return {"body": {"error": "Nenhum experimento ativo encontrado."}}

        # Último FINISHED global
        runs_df = mlflow.search_runs(
            experiment_ids=exp_ids,
            filter_string="attributes.status = 'FINISHED'",
            order_by=["attributes.start_time DESC"],
            max_results=1,
        )

        # Fallback: último global sem filtro
        if runs_df.empty:
            runs_df = mlflow.search_runs(
                experiment_ids=exp_ids,
                order_by=["attributes.start_time DESC"],
                max_results=1,
            )
            if runs_df.empty:
                return {"body": {"error": "Nenhum run encontrado em nenhum experimento."}}

        return _extract_run_payload(runs_df, client)

    except Exception as e:
        return {"body": {"error": str(e), "error_type": type(e).__name__}}


def get_model_metrics(experiment_name: str) -> dict:
    """
    Conecta ao MLflow Tracking Server (via ARN) e retorna métricas do último run FINISHED
    do experimento informado; se não houver FINISHED, pega o último run qualquer.
    """
    if not experiment_name:
        return {"body": {"error": "experiment_name vazio. Forneça o nome do experimento."}}

    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_ARN)
        mlflow.set_experiment(experiment_name)

        # Busca o último FINISHED do experimento
        runs_df = mlflow.search_runs(
            filter_string="attributes.status = 'FINISHED'",
            order_by=["attributes.start_time DESC"],
            max_results=1
        )

        # Fallback: último run do experimento
        if runs_df.empty:
            runs_df = mlflow.search_runs(
                order_by=["attributes.start_time DESC"],
                max_results=1
            )
            if runs_df.empty:
                return {"body": {"error": f"Nenhum run encontrado para o experimento '{experiment_name}'."}}

        client = MlflowClient()
        payload = _extract_run_payload(runs_df, client)
        # Garante que o nome do experimento é o informado
        if isinstance(payload, dict) and "body" in payload and "experiment" in payload["body"]:
            payload["body"]["experiment"]["name"] = experiment_name
        return payload

    except Exception as e:
        return {"body": {"error": str(e), "error_type": type(e).__name__}}