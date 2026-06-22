# ==============================================================================
# Lambda Training Launcher - Container Image
# ==============================================================================
# Imagem para Lambda que lanca jobs de treinamento SageMaker
#
# Build:
#   docker build -t training-launcher .
#
# Push para ECR (dev):
#   aws ecr get-login-password --region us-east-1 --profile elo | docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-1.amazonaws.com
#   docker tag training-launcher:latest 888577064416.dkr.ecr.us-east-1.amazonaws.com/training-launcher-dev:latest
#   docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/training-launcher-dev:latest
# ==============================================================================

FROM public.ecr.aws/lambda/python:3.12

# Copiar requirements e instalar dependencias Python
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copiar codigo da Lambda
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Handler
CMD ["handler.lambda_handler"]
