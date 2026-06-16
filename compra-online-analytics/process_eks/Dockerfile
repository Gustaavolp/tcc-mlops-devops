FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY services/process_eks/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY classes/ ./classes/

COPY services/process_eks/ .

CMD ["python", "main.py"]