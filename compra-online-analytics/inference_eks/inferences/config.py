import os

# AWS
REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo"
DYNAMO_TABLE = "elo-fraud-customer-recent-tx-dev"

# Model
MODEL_URI = "s3://sagemaker-us-east-1-888577064416/22/models/m-9c1b7f26f74c4ec08c66c73a4a59ab75/artifacts/"
TRACKING_URI = "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ"
MODEL_NAME = "Felicidade"
# Logs
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"