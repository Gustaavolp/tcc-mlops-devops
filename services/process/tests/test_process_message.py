"""Testes do worker assíncrono: cada mensagem da fila vai para o data lake e para a feature store."""
import pytest

import main


class FakeFirehose:
    def __init__(self, fail=False):
        self.records, self.fail = [], fail

    def put_record(self, body):
        if self.fail:
            raise RuntimeError("firehose indisponível")
        self.records.append(body)


class FakeDynamo:
    def __init__(self, result=True):
        self.calls, self.result = [], result

    def save_event(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


@pytest.fixture
def fakes(monkeypatch):
    fh, db = FakeFirehose(), FakeDynamo()
    monkeypatch.setattr(main, "firehose", fh)
    monkeypatch.setattr(main, "db", db)
    monkeypatch.setattr(main, "send_metric", lambda *a, **k: None)
    return fh, db


def msg(**extra):
    body = {"CARDHOLDER_ACCOUNT_IDENTIFIER": "u-1", "3DS_TRANS_ID": "tx-1", "score": 0.7}
    body.update(extra)
    return body


def test_grava_no_data_lake_e_na_feature_store(fakes):
    fh, db = fakes
    assert main.process_message(msg(PURCHASE_DATE_AND_TIME="2026-02-16 22:00:00")) is True
    assert len(fh.records) == 1
    (call,) = db.calls
    assert call["acctID"] == "u-1"
    assert call["threeDSServerTransID"] == "tx-1"
    assert call["n_keep"] == 15                      # janela das 15 últimas transações
    assert call["payload_dict"]["score"] == 0.7


def test_preenche_data_da_compra_ausente(fakes):
    _, db = fakes
    main.process_message(msg())
    assert isinstance(db.calls[0]["payload_dict"]["PURCHASE_DATE_AND_TIME"], float)


def test_mensagem_sem_identificadores_nao_vai_para_dynamo(fakes):
    fh, db = fakes
    assert main.process_message({"score": 0.1}) is False
    assert db.calls == []
    assert len(fh.records) == 1                      # ainda é registrada no data lake


def test_falha_no_firehose_nao_impede_gravacao_no_dynamo(monkeypatch, fakes):
    _, db = fakes
    monkeypatch.setattr(main, "firehose", FakeFirehose(fail=True))
    assert main.process_message(msg()) is True
    assert len(db.calls) == 1


def test_falha_no_dynamo_retorna_false(monkeypatch, fakes):
    monkeypatch.setattr(main, "db", FakeDynamo(result=False))
    assert main.process_message(msg()) is False
