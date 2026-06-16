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