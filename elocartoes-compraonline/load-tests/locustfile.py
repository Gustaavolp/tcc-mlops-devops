# =============================================================================
# Locust Load Test - Elo Fraud Detection API
# =============================================================================
# Usa 100 payloads REAIS de transacoes 3DS (output 1.json)
# Cada payload e enviado EXATAMENTE como esta no arquivo, sem alteracao.
#
# INTERFACE WEB: locust -f locustfile.py
# Acesse: http://localhost:8089
#
# CONFIGURACAO:
#   - 1 usuario = 1 RPS
#   - Para 100 RPS, configure 100 usuarios na interface web
# =============================================================================

from locust import HttpUser, task, constant_throughput, events
import json
import os
from threading import Lock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACOES
# =============================================================================

# API Keys por ambiente
API_KEYS = {
    "dev": "IY8EB31x6z69IzAGJqMXb6pIZARnZOSP4vMuvj5W",
    "staging": "6QTQjhwTLn9M4GU9uz6m5IqvK2SVqyy8DZ1jlTri",
}

# Hosts por ambiente (atualizado 2026-02-18 via AWS CLI)
HOSTS = {
    "dev": "https://3papa9zzq5.execute-api.us-east-1.amazonaws.com",
    "staging": "https://4x88z39gl4.execute-api.sa-east-1.amazonaws.com",
}

# Detecta ambiente pelo host
def get_api_key(host):
    if "3papa9zzq5" in host or "us-east-1" in host:
        return API_KEYS.get("dev", "")
    if "4x88z39gl4" in host or "sa-east-1" in host:
        return API_KEYS.get("staging", "")
    return API_KEYS.get("staging", "")


# =============================================================================
# CARREGAMENTO DOS PAYLOADS REAIS
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAYLOAD_FILE = os.path.join(SCRIPT_DIR, "..", "output 1.json")

try:
    with open(PAYLOAD_FILE) as f:
        PAYLOADS = json.load(f)
    logger.info(f"Carregados {len(PAYLOADS)} payloads reais de: {PAYLOAD_FILE}")
except FileNotFoundError:
    logger.error(f"Arquivo nao encontrado: {PAYLOAD_FILE}")
    logger.error("Coloque o arquivo 'output 1.json' na raiz do projeto.")
    PAYLOADS = []


# =============================================================================
# SELETOR ROUND-ROBIN (thread-safe)
# =============================================================================

class PayloadSelector:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._index = 0
                    cls._instance._index_lock = Lock()
        return cls._instance

    def next_payload(self) -> dict:
        if not PAYLOADS:
            return {}
        with self._index_lock:
            payload = PAYLOADS[self._index % len(PAYLOADS)]
            self._index += 1
            return payload

    @property
    def total_sent(self) -> int:
        return self._index


selector = PayloadSelector()


# =============================================================================
# USUARIO - 1 USUARIO = 1 RPS
# =============================================================================

class FraudDetectionUser(HttpUser):
    """
    Usuario para teste de carga com payloads reais.

    IMPORTANTE: 1 usuario = 1 RPS

    Na interface web (http://localhost:8089):
    - Para 50 RPS  -> configure 50 usuarios
    - Para 100 RPS -> configure 100 usuarios
    - Para 200 RPS -> configure 200 usuarios
    """

    # 1 request por segundo por usuario
    wait_time = constant_throughput(1)

    # Host padrao: DEV (override com --host ou LOCUST_ENV=staging)
    host = HOSTS.get(os.environ.get("LOCUST_ENV", "dev"), HOSTS["dev"])

    def on_start(self):
        """Configura headers com API key no inicio."""
        self.api_key = get_api_key(self.host)

    @task
    def score_real_payload(self):
        """Envia payload real (round-robin pelos 100 payloads)."""
        payload = selector.next_payload()
        if not payload:
            return

        tx_id = payload.get("threeDSServerTransID", "unknown")

        with self.client.post(
            "/v1/authorize-purchase",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            },
            name="POST /v1/authorize-purchase",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "score" in data:
                        response.success()
                    else:
                        response.failure("Campo 'score' ausente")
                except Exception as e:
                    response.failure(f"JSON invalido: {e}")
            elif response.status_code == 403:
                response.failure("403 Forbidden - API key invalida")
            else:
                response.failure(f"HTTP {response.status_code}")


# =============================================================================
# EVENTOS
# =============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("LOAD TEST INICIADO - PAYLOADS REAIS")
    logger.info(f"Target: {environment.host}")
    logger.info(f"Payloads carregados: {len(PAYLOADS)}")
    logger.info(f"Selecao: Round-robin")
    logger.info("1 usuario = 1 RPS")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("LOAD TEST FINALIZADO")
    logger.info(f"Total de payloads enviados: {selector.total_sent}")
    logger.info(f"Ciclos completos dos 100 payloads: {selector.total_sent // max(len(PAYLOADS), 1)}")
    logger.info("=" * 60)


# =============================================================================
# COMO USAR
# =============================================================================
#
# 1. Iniciar interface web:
#    locust -f locustfile.py
#
# 2. Acessar: http://localhost:8089
#
# 3. Configurar na interface:
#    - Number of users: quantidade de RPS desejado (ex: 100)
#    - Spawn rate: quantos usuarios criar por segundo (ex: 10)
#    - Host: ja esta configurado para DEV
#
# 4. Clicar em "Start swarming"
#
# EXEMPLOS:
#   50 RPS  -> 50 users,  spawn rate 10
#   100 RPS -> 100 users, spawn rate 20
#   200 RPS -> 200 users, spawn rate 50
#
# VIA CLI (headless):
#   locust -f locustfile.py --headless --users 10 --spawn-rate 5 --run-time 30s
#
# =============================================================================
