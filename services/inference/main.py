
import asyncio
import logging
import sys
import warnings
from typing import Dict, Any
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
 
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
 
from inferences.config import LOG_FORMAT, TRACKING_URI, MODEL_NAME, QUEUE_URL
from boto3.dynamodb.conditions import Key
from classes.model_service import ModelService
from classes.sqs_publisher import SQSPublisher

from classes.real_feature_store import OnlineFeatureStore
from classes.normalize_payload import PayloadNormalizer
 
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
 
# Serviços globais (inicializados no startup)

model_service = None
publisher = None
feature_store = None
payload_normalizer = None
sqs_executor = None
 

def json_to_model(payload):
    return feature_store.enrich_payload(payload_normalizer.normalize_request(payload))


async def _keep_connections_warm():
    """Mantém conexões AWS vivas com chamadas read-only a cada 30s."""
    while True:
        await asyncio.sleep(30)
        try:
            feature_store.table.query(
                KeyConditionExpression=Key("acctID").eq("__keepalive__"),
                Limit=1
            )
            publisher.sqs.get_queue_attributes(
                QueueUrl=QUEUE_URL,
                AttributeNames=["ApproximateNumberOfMessages"]
            )
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa serviços no startup."""
    global model_service, publisher, feature_store, payload_normalizer, sqs_executor

    try:
        logging.info("Inicializando serviços...")

        model_service = ModelService(TRACKING_URI, MODEL_NAME)
        publisher = SQSPublisher()
        feature_store = OnlineFeatureStore()
        payload_normalizer = PayloadNormalizer()
        sqs_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sqs")
        logging.info("Serviços inicializados com sucesso.")
    except Exception as e:
        logging.critical(f"Falha na inicialização: {e}")
        sys.exit(1)

    # Warmup: força abertura de conexões TCP/TLS (lazy connections do boto3)
    try:
        feature_store.table.query(
            KeyConditionExpression=Key("acctID").eq("__warmup__"),
            Limit=1
        )
        publisher.sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL,
            AttributeNames=["ApproximateNumberOfMessages"]
        )
        logging.info("Warmup de conexões concluído.")
    except Exception as e:
        logging.warning(f"Warmup falhou (não-fatal): {e}")

    # Keep-alive: mantém conexões AWS quentes em background
    keepalive_task = asyncio.create_task(_keep_connections_warm())
    logging.info("Keep-alive de conexões iniciado (intervalo: 30s).")

    yield

    # Cleanup: cancela keep-alive e encerra executor SQS
    keepalive_task.cancel()
    sqs_executor.shutdown(wait=True, cancel_futures=False)
    logging.info("Encerrando aplicação.")
 
 
app = FastAPI(title="Fraud Inference API", lifespan=lifespan)
 
 
@app.get("/health")
def health():
    """Health check para Kubernetes probes."""
    if model_service is None or model_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}
 
 
@app.post("/v1/authorize-purchase")
def score(payload: Dict[str, Any]):
    """
    Endpoint de inferência de fraude.
    Recebe payload da transação e retorna score.
    """
    try:
        # 1. Processamento e enriquecimento
        processed = json_to_model(payload)

        # 2. Inferência
        response_model = model_service.predict_proba([processed])
        score_value = response_model[0][1]

        # 3. Monta resposta
        processed['3DS_TRANS_ID'] = payload.get('threeDSServerTransID')
        processed["score"] = score_value
        processed["threshold"] = model_service.threshold
        processed["FLAG_FRAUD"] = True if score_value >= model_service.threshold else False

        # 4. Publica no SQS em background (fire-and-forget)
        sqs_executor.submit(publisher.publish, processed)

        return JSONResponse(content={
            "transaction_id": processed.get("3DS_TRANS_ID"),
            "score": score_value,
            "fraud_label": processed["FLAG_FRAUD"]
        })
 
    except Exception as e:
        logging.error(f"Erro no scoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
if __name__ == "__main__":
    import uvicorn

    # timeout_keep_alive DEVE ser maior que o NLB idle timeout (350s default).
    # Se uvicorn fechar a conexao antes do NLB, requests chegam em sockets fechados
    # causando 502/504 intermitentes (race condition NLB vs backend).
    # Cadeia: API GW REST (idle 310s, fixo) -> NLB (idle 350s) -> uvicorn (380s)
    #
    # workers=2: 2 processos independentes (cada um com seu proprio GIL, modelo,
    # conexoes boto3, warmup e keep-alive). Dobra throughput para workloads CPU-bound
    # (numpy, XGBoost). Cada worker consome ~275Mi RAM (total ~550Mi, dentro do limit 1.5Gi).
    uvicorn.run("main:app", host="0.0.0.0", port=8000, timeout_keep_alive=380, workers=2)