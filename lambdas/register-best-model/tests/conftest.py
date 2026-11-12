import os

# Configuração lida por envs.py no import (equivalente às variáveis da Lambda)
os.environ.update({
    "MODEL_NAME": "Felicidade",
    "METRIC_TO_COMPARE": "metrics.f1_oot",
    "MLFLOW_TRACKING_URI": "file:///tmp/mlruns-test",
    "MLFLOW_BEST_MODEL_RUN": "best_estimator",
    "MLFLOW_TARGET_TAG_KEY": "stage",
    "MLFLOW_TARGET_TAG": "prod",
    "ENVIRONMENT": "dev",
})
