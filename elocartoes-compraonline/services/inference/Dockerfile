FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Criar usuario non-root para seguranca
# UID/GID 1000 alinhado com securityContext do Kubernetes
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copiar requirements e instalar dependencias (como root)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar codigo da aplicacao
COPY classes/ ./classes/
COPY inferences/ ./inferences/
COPY main.py .

# Ajustar permissoes do diretorio /app para o usuario appuser
RUN chown -R appuser:appgroup /app

# Trocar para usuario non-root
USER appuser

# Expor porta HTTP
EXPOSE 8000

CMD ["python", "main.py"]