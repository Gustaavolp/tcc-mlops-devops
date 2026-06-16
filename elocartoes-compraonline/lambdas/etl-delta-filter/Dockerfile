# ==============================================================================
# Lambda ETL Delta Filter - Container Image
# ==============================================================================
# Imagem otimizada para processar Delta Lake com pyarrow
#
# Build:
#   docker build -t etl-delta-filter .
#
# Push para ECR (dev):
#   aws ecr get-login-password --region us-east-1 --profile elo | docker login --username AWS --password-stdin 888577064416.dkr.ecr.us-east-1.amazonaws.com
#   docker tag etl-delta-filter:latest 888577064416.dkr.ecr.us-east-1.amazonaws.com/etl-delta-filter-dev:latest
#   docker push 888577064416.dkr.ecr.us-east-1.amazonaws.com/etl-delta-filter-dev:latest
# ==============================================================================

FROM public.ecr.aws/lambda/python:3.12

# Instalar dependencias do sistema para pyarrow
RUN dnf install -y gcc-c++ && dnf clean all

# Copiar requirements e instalar dependencias Python
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copiar codigo da Lambda
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Handler
CMD ["handler.lambda_handler"]
