import boto3
import json
import uuid
import logging
from typing import Dict, Any
from inferences.config import REGION, QUEUE_URL

class SQSPublisher:
    def __init__(self):
        self.sqs = boto3.client("sqs", region_name=REGION)

    def publish(self, payload: Dict[str, Any]):
        try:
            payload_json = json.dumps(payload, default=str)
            tx_id = str(payload.get("3DS_TRANS_ID", uuid.uuid4()))
            
            self.sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=payload_json,
                MessageGroupId=str(payload.get("CARDHOLDER_ACCOUNT_IDENTIFIER") or tx_id),
                MessageDeduplicationId=tx_id
            )
            logging.info(f"SQS Enviado: {tx_id}")
        except Exception as e:
            logging.error(f"Erro SQS: {e}")