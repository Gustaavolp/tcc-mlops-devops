"""Testes do disparo de Training Jobs (SageMaker substituído por dublê)."""
import pytest

import handler


class FakeTrainer:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs, self.wait = kwargs, None
        FakeTrainer.instances.append(self)

    def train(self, wait=True):
        self.wait = wait


class FakeSSM:
    def __init__(self, value):
        self.value, self.names = value, []

    def get_parameter(self, Name):
        self.names.append(Name)
        return {"Parameter": {"Value": self.value}}


@pytest.fixture(autouse=True)
def fake_trainer(monkeypatch):
    FakeTrainer.instances = []
    monkeypatch.setattr(handler, "ModelTrainer", FakeTrainer)
    monkeypatch.setattr(handler, "SAGEMAKER_ROLE", "arn:aws:iam::123456789012:role/sm")
    monkeypatch.setattr(handler, "DATA_S3_PATH", "s3://bucket/training_zone/")
    monkeypatch.setattr(handler, "MLFLOW_URI", "arn:mlflow")


def test_usa_imagem_do_parametro_ssm(monkeypatch):
    ssm = FakeSSM("123.dkr.ecr.us-east-1.amazonaws.com/model:abc123")
    monkeypatch.setattr(handler, "TRAINING_IMAGE_PARAM", "/elo-fraud/dev/training-image")
    monkeypatch.setattr(handler.boto3, "client", lambda svc: ssm)
    handler.lambda_handler({}, None)
    assert ssm.names == ["/elo-fraud/dev/training-image"]
    assert all(t.kwargs["training_image"].endswith(":abc123") for t in FakeTrainer.instances)


def test_sem_parametro_usa_variavel_training_image(monkeypatch):
    monkeypatch.setattr(handler, "TRAINING_IMAGE_PARAM", None)
    monkeypatch.setattr(handler, "TRAINING_IMAGE", "repo/model:latest")
    handler.lambda_handler({}, None)
    assert FakeTrainer.instances[0].kwargs["training_image"] == "repo/model:latest"


def test_sem_imagem_configurada_falha(monkeypatch):
    monkeypatch.setattr(handler, "TRAINING_IMAGE_PARAM", None)
    monkeypatch.setattr(handler, "TRAINING_IMAGE", None)
    with pytest.raises(ValueError):
        handler.lambda_handler({}, None)


def test_um_job_por_combinacao_sem_aguardar(monkeypatch):
    monkeypatch.setattr(handler, "TRAINING_IMAGE_PARAM", None)
    monkeypatch.setattr(handler, "TRAINING_IMAGE", "repo/model:latest")
    out = handler.lambda_handler({}, None)
    expected = len(handler.models) * len(handler.imputers) * len(handler.reducoes) * len(handler.imbalances)
    assert out["total_jobs"] == expected == len(FakeTrainer.instances)
    t = FakeTrainer.instances[0]
    assert t.wait is False                                      # disparo assíncrono
    hp = t.kwargs["hyperparameters"]
    assert hp["model_name"] == "XGBClassifier" and hp["imbalance_name"] == "SMOTE"
    assert hp["path_s3_data"] == "s3://bucket/training_zone/"
    assert t.kwargs["role"] == "arn:aws:iam::123456789012:role/sm"
