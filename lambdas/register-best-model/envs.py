import os
from dotenv import load_dotenv

load_dotenv()

class Envs:

    MODEL_NAME = os.getenv("MODEL_NAME")
    METRIC_TO_COMPARE = os.getenv("METRIC_TO_COMPARE")
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
    MLFLOW_BEST_MODEL_RUN = os.getenv("MLFLOW_BEST_MODEL_RUN")
    MLFLOW_TARGET_TAG_KEY = os.getenv("MLFLOW_TARGET_TAG_KEY")
    MLFLOW_TARGET_TAG = os.getenv("MLFLOW_TARGET_TAG")

    # Evento publicado no EventBridge quando uma nova versão é registrada; aciona
    # o rolling restart do serviço de inferência (projeto CodeBuild model-rollout).
    ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
    PROMOTION_EVENT_BUS = os.getenv("PROMOTION_EVENT_BUS", "default")
    PROMOTION_EVENT_SOURCE = os.getenv("PROMOTION_EVENT_SOURCE", "elo-fraud.mlops")
    PUBLISH_PROMOTION_EVENT = os.getenv("PUBLISH_PROMOTION_EVENT", "true").lower() == "true"
