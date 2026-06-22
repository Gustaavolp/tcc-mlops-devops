# =============================================================================
# Dockerfile - Lambda Register Best Model
# =============================================================================
# Esta Lambda consulta o MLflow, identifica o melhor modelo baseado em
# training_f1_score e registra no Model Registry.
#
# Build:
#   docker build -t best-model-register .
#
# Test local:
#   docker run -p 9000:8080 \
#     -e MODEL_NAME=Felicidade \
#     -e METRIC_TO_COMPARE=metrics.f1_oot \
#     -e MLFLOW_TRACKING_URI=<mlflow-uri> \
#     -e MLFLOW_BEST_MODEL_RUN=best_estimator \
#     -e MLFLOW_TARGET_TAG_KEY=stage \
#     -e MLFLOW_TARGET_TAG=prod \
#     best-model-register
#
#   curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
#     -d '{}'
# =============================================================================

FROM public.ecr.aws/lambda/python:3.12

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo da Lambda
COPY lambda_handler.py /var/task/
COPY best_model_register.py /var/task/
COPY envs.py /var/task/
COPY utils.py /var/task/

# Handler da Lambda
CMD ["lambda_handler.lambda_handler"]
