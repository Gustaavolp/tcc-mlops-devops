"""Testes da API de inferência com serviços substituídos por dublês (sem AWS/MLflow)."""
import pytest
from fastapi.testclient import TestClient

import main
from classes.normalize_payload import PayloadNormalizer


class FakeModel:
    def __init__(self, proba):
        self.model = object()
        self.threshold = 0.5
        self._proba = proba

    def predict_proba(self, rows):
        assert len(rows) == 1
        return [[1 - self._proba, self._proba]]


class FakeFeatureStore:
    def enrich_payload(self, normalized):
        enriched = dict(normalized)
        enriched["feat_user_tx_count_10"] = 3.0
        return enriched


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def submit(self, fn, *args):
        self.calls.append((fn, args))


class FakePublisher:
    def publish(self, payload):  # pragma: no cover - chamado via executor
        pass


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "payload_normalizer", PayloadNormalizer())
    monkeypatch.setattr(main, "feature_store", FakeFeatureStore())
    monkeypatch.setattr(main, "publisher", FakePublisher())
    monkeypatch.setattr(main, "sqs_executor", FakeExecutor())
    # sem "with": o lifespan (que conecta em AWS/MLflow) não é executado
    return TestClient(main.app)


PAYLOAD = {"threeDSServerTransID": "tx-1", "purchaseAmount": "99.9", "acctID": "u-1"}


def test_health_503_sem_modelo_carregado(client, monkeypatch):
    monkeypatch.setattr(main, "model_service", None)
    assert client.get("/health").status_code == 503


def test_health_200_com_modelo_carregado(client, monkeypatch):
    monkeypatch.setattr(main, "model_service", FakeModel(0.1))
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


@pytest.mark.parametrize("proba,label", [(0.8, True), (0.5, True), (0.2, False)])
def test_scoring_aplica_threshold(client, monkeypatch, proba, label):
    monkeypatch.setattr(main, "model_service", FakeModel(proba))
    r = client.post("/v1/authorize-purchase", json=PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body == {"transaction_id": "tx-1", "score": proba, "fraud_label": label}


def test_scoring_publica_resultado_na_fila(client, monkeypatch):
    monkeypatch.setattr(main, "model_service", FakeModel(0.9))
    client.post("/v1/authorize-purchase", json=PAYLOAD)
    calls = main.sqs_executor.calls
    assert len(calls) == 1
    fn, (published,) = calls[0]
    assert fn == main.publisher.publish
    assert published["3DS_TRANS_ID"] == "tx-1"
    assert published["score"] == 0.9
    assert published["FLAG_FRAUD"] is True
    assert published["AMOUNT"] == 99.9


def test_scoring_retorna_500_em_falha_do_modelo(client, monkeypatch):
    class Broken(FakeModel):
        def predict_proba(self, rows):
            raise RuntimeError("falha no modelo")

    monkeypatch.setattr(main, "model_service", Broken(0.5))
    r = client.post("/v1/authorize-purchase", json=PAYLOAD)
    assert r.status_code == 500
    assert main.sqs_executor.calls == []
