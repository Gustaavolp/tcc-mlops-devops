"""Testes da promoção condicional no Model Registry e do evento que aciona o rollout."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest
from mlflow.exceptions import MlflowException

import best_model_register as bmr


class FakeClient:
    def __init__(self, registered_metric=None, missing=False):
        self.registered_metric, self.missing = registered_metric, missing

    def search_experiments(self, **kwargs):
        return [SimpleNamespace(experiment_id="7")]

    def get_registered_model(self, name):
        if self.missing:
            raise MlflowException("RESOURCE_DOES_NOT_EXIST: modelo não encontrado")
        if self.registered_metric is None:
            return SimpleNamespace(latest_versions=[])
        return SimpleNamespace(latest_versions=[SimpleNamespace(run_id="run-old")])

    def get_run(self, run_id):
        return SimpleNamespace(data=SimpleNamespace(metrics={"f1_oot": self.registered_metric}))


class FakeEvents:
    def __init__(self, fail=False):
        self.entries, self.fail = [], fail

    def put_events(self, Entries):
        if self.fail:
            raise RuntimeError("EventBridge indisponível")
        self.entries.extend(Entries)
        return {"FailedEntryCount": 0, "Entries": [{"EventId": "1"}]}


@pytest.fixture
def setup(monkeypatch):
    def _setup(candidate_metric=0.80, registered_metric=None, missing=False, events_fail=False):
        events = FakeEvents(fail=events_fail)
        registered = []
        monkeypatch.setattr(bmr, "MlflowClient", lambda tracking_uri=None: FakeClient(registered_metric, missing))
        monkeypatch.setattr(bmr.mlflow, "set_tracking_uri", lambda uri: None)
        monkeypatch.setattr(bmr.mlflow, "search_runs", lambda **kw: pd.DataFrame(
            [{"run_id": "run-new", "metrics.f1_oot": candidate_metric}]))

        def register_model(model_uri, name):
            registered.append((model_uri, name))
            return SimpleNamespace(version=3)

        monkeypatch.setattr(bmr.mlflow, "register_model", register_model)
        monkeypatch.setattr(bmr.boto3, "client", lambda service, **kw: events)
        return events, registered
    return _setup


def run():
    out = bmr.MlflowModelRegistry().register_best_model()
    return out["statusCode"], json.loads(out["body"])


def test_registra_quando_candidato_supera_versao_atual(setup):
    events, registered = setup(candidate_metric=0.85, registered_metric=0.80)
    status, body = run()
    assert status == 200 and body["version"] == "3"
    assert registered == [("runs:/run-new/best_estimator", "Felicidade")]
    (entry,) = events.entries
    assert entry["Source"] == "elo-fraud.mlops"
    assert entry["DetailType"] == "ModelVersionRegistered"
    detail = json.loads(entry["Detail"])
    assert detail == {"model_name": "Felicidade", "version": "3", "run_id": "run-new",
                      "metric": "metrics.f1_oot", "metric_value": 0.85, "environment": "dev"}
    assert body["event_published"] is True


def test_nao_registra_quando_candidato_e_inferior(setup):
    events, registered = setup(candidate_metric=0.70, registered_metric=0.80)
    status, body = run()
    assert status == 200 and "No model is eligible" in body["message"]
    assert registered == [] and events.entries == []


def test_registra_primeira_versao_quando_modelo_nao_existe(setup):
    events, registered = setup(missing=True)
    status, _ = run()
    assert status == 200 and len(registered) == 1 and len(events.entries) == 1


def test_registra_quando_modelo_nao_tem_versoes(setup):
    _, registered = setup(registered_metric=None)
    assert run()[0] == 200 and len(registered) == 1


def test_falha_no_evento_nao_desfaz_registro(setup):
    _, registered = setup(candidate_metric=0.9, registered_metric=0.8, events_fail=True)
    status, body = run()
    assert status == 200 and len(registered) == 1
    assert body["event_published"] is False


def test_sem_experimento_de_producao_retorna_404(setup, monkeypatch):
    setup()
    monkeypatch.setattr(FakeClient, "search_experiments", lambda self, **kw: [])
    assert run()[0] == 404
