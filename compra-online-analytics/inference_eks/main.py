
import logging
import sys
import warnings
from typing import Dict, Any
from contextlib import asynccontextmanager
 
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
 
from inferences.config import LOG_FORMAT, TRACKING_URI, MODEL_NAME
from classes.model_service import ModelService
from classes.sqs_publisher import SQSPublisher

from classes.real_feature_store import OnlineFeatureStore
from classes.normalize_payload import PayloadNormalizer
 
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
 
# Serviços globais (inicializados no startup)

model_service = None
publisher = None
 

def json_to_model(payload):
    payload_normalizer = PayloadNormalizer()
    online_feature_store = OnlineFeatureStore()

    return online_feature_store.enrich_payload(payload_normalizer.normalize_request(payload))
    
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa serviços no startup."""
    global  model_service, publisher
 
    try:
        logging.info("Inicializando serviços...")

        model_service = ModelService(TRACKING_URI, MODEL_NAME)
        publisher = SQSPublisher()
        logging.info("Serviços inicializados com sucesso.")
    except Exception as e:
        logging.critical(f"Falha na inicialização: {e}")
        sys.exit(1)
 
    yield
 
    logging.info("Encerrando aplicação.")
 
 
app = FastAPI(title="Fraud Inference API", lifespan=lifespan)
 
 
@app.get("/health")
async def health():
    """Health check para Kubernetes probes."""
    if model_service is None or model_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}
 
 
@app.post("/v1/score")
async def score(payload: Dict[str, Any]):
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
        processed["FLAG_FRAUD"] = True if score_value >= model_service.threshold else False
 
        # 4. Publica no SQS (async log)
        publisher.publish(processed)
 
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
    uvicorn.run(app, host="0.0.0.0", port=8000)