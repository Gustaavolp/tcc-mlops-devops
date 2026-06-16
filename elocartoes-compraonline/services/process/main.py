import boto3
import json
import os
import time
import sys
import logging
from botocore.exceptions import ClientError

# Importa as SUAS classes (certifique-se que estão na pasta classes/)
from classes.dynamo_functions import DynamoEventTable
from classes.firehose_functions import FirehoseClient

# --- CONFIGURAÇÕES ---
REGION = os.getenv("AWS_REGION", "us-east-1")
# Ajuste com a URL correta da sua fila
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/888577064416/elo-fraud-resultset-dev.fifo")
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE", "elo-fraud-customer-recent-tx-dev")
FIREHOSE_STREAM_NAME = os.getenv("FIREHOSE_STREAM", "elo-fraud-inference-firehose-dev")
NAMESPACE_METRICS = "EloFraud/Process"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- INICIALIZAÇÃO ---
try:
    sqs = boto3.client("sqs", region_name=REGION)
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    
    # Inicializa suas classes
    db = DynamoEventTable(DYNAMO_TABLE_NAME, region=REGION)
    firehose = FirehoseClient(FIREHOSE_STREAM_NAME, region=REGION)
    
    logging.info("Classes DynamoEventTable e FirehoseClient iniciadas.")
except Exception as e:
    logging.critical(f"Erro ao iniciar clientes: {e}")
    sys.exit(1)

def send_metric(name, value=1.0):
    """Envia métricas para o CloudWatch"""
    try:
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE_METRICS,
            MetricData=[{'MetricName': name, 'Value': value, 'Unit': 'Count'}]
        )
    except: pass

def process_message(body_dict):
    """
    Processa a mensagem usando as classes utilitárias do projeto.
    """
    # 1. DATA LAKE (Firehose)
    try:
        # Usa sua classe FirehoseClient
        firehose.put_record(body_dict)
    except Exception as e:
        logging.error(f"Erro Firehose: {e}")
    
    # 2. FEATURE STORE (DynamoDB)
    user_id = body_dict.get("CARDHOLDER_ACCOUNT_IDENTIFIER")
    tx_id = body_dict.get("3DS_TRANS_ID")
    
    if "PURCHASE_DATE_AND_TIME" not in body_dict:
        body_dict["PURCHASE_DATE_AND_TIME"] = time.time()
    
    if user_id and tx_id:
        try:
            # Usa sua classe DynamoEventTable
            # Ela já lida com Idempotência (Update) e Rotação (Delete antigos)
            success = db.save_event(
                acctID=str(user_id),
                threeDSServerTransID=str(tx_id),
                payload_dict=body_dict,
                n_keep=15 # Garante janela de 15
            )
            
            if success:
                logging.info(f"DynamoDB salvo (Via Class): User {user_id}")
                send_metric("DynamoSaved")
                return True
            else:
                logging.error(f"Falha no save_event para {user_id}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao chamar db.save_event: {e}")
            return False
    else:
        logging.warning(f"Payload sem User ID ou Tx ID. Ignorado no Dynamo.")
        return False

def run():
    logging.info(f"Worker Iniciado na fila: {SQS_QUEUE_URL}")
    
    while True:
        try:
            # Long Polling (espera até 20s por mensagem)
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20, 
                AttributeNames=['All']
            )

            messages = response.get("Messages", [])

            if not messages:
                continue

            for msg in messages:
                receipt_handle = msg["ReceiptHandle"]
                try:
                    body_str = msg["Body"]
                    body = json.loads(body_str)
                    
                    # Processa
                    if process_message(body):
                        send_metric("Success")
                    
                    # Deleta (Ack)
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
                    
                except json.JSONDecodeError:
                    logging.error("JSON inválido na fila")
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
                except Exception as e:
                    logging.error(f"Erro genérico ao processar msg: {e}")
                    # Não deleta para cair na DLQ se for erro transiente

        except Exception as e:
            logging.error(f"Erro no loop SQS: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()