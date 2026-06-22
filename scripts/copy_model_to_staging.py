#!/usr/bin/env python3
# =============================================================================
# Copy MLflow Model "Felicidade" from DEV to STAGING
# =============================================================================
# Usa MLflow API para conectar ao DEV MLflow App (mlflow-app/app-LNOFZM2USGXQ)
# e copiar o modelo XGBClassifier Pipeline real para o STAGING tracking server.
#
# O script antigo escaneava o bucket S3 errado (elo-fraud-mlflow-artifacts-dev)
# que so continha prototipos RandomForest (4 features). Este script conecta ao
# MLflow App correto onde vive o modelo "Felicidade" (64 features, binary).
#
# Requisitos:
#   pip install mlflow boto3 sagemaker-mlflow pyyaml
#
# Variaveis de ambiente:
#   DEV_MLFLOW_TRACKING_SERVER_ARN    - ARN do DEV MLflow App
#   STAGING_MLFLOW_TRACKING_SERVER_ARN - ARN do tracking server staging
#   MODEL_NAME                         - nome do modelo (default "Felicidade")
#   FORCE_COPY                         - "true" para forcar copia mesmo se existir
# =============================================================================

import os
import sys
import tempfile
import logging

import yaml
import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =====================================================================
# Configuracao
# =====================================================================
DEV_TRACKING_SERVER_ARN = os.environ.get(
    "DEV_MLFLOW_TRACKING_SERVER_ARN",
    "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ"
)
DEV_REGION = "us-east-1"

STAGING_TRACKING_SERVER_ARN = os.environ.get(
    "STAGING_MLFLOW_TRACKING_SERVER_ARN",
    "arn:aws:sagemaker:sa-east-1:888577064416:mlflow-tracking-server/elo-fraud-mlflow-staging"
)

MODEL_NAME = os.environ.get("MODEL_NAME", "Felicidade")
EXPERIMENT_NAME = "model-copy-from-dev"

# Fallback S3 - bucket onde o MLflow App DEV armazena artifacts
DEV_FALLBACK_BUCKET = "sagemaker-us-east-1-888577064416"
DEV_FALLBACK_PREFIX = "38/models/"


def download_model_from_s3(bucket, region, local_dir):
    """Fallback: baixa model artifacts direto do S3 do MLflow App DEV."""
    s3 = boto3.client("s3", region_name=region)
    paginator = s3.get_paginator("list_objects_v2")

    # Encontra diretorios de modelo
    model_dirs = []
    for page in paginator.paginate(Bucket=bucket, Prefix=DEV_FALLBACK_PREFIX, Delimiter="/"):
        for prefix in page.get("CommonPrefixes", []):
            model_dir_prefix = prefix["Prefix"]
            artifacts_prefix = f"{model_dir_prefix}artifacts/"

            try:
                resp = s3.list_objects_v2(
                    Bucket=bucket,
                    Prefix=f"{artifacts_prefix}model/MLmodel",
                    MaxKeys=1
                )
                if resp.get("Contents"):
                    model_dirs.append({
                        "prefix": artifacts_prefix,
                        "last_modified": resp["Contents"][0]["LastModified"]
                    })
            except Exception:
                pass

    if not model_dirs:
        logger.error("Nenhum artifact de modelo encontrado no S3 fallback")
        return None

    latest = max(model_dirs, key=lambda x: x["last_modified"])
    model_prefix = f"{latest['prefix']}model/"

    count = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=model_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            relative = key[len(model_prefix):]
            if not relative:
                continue
            local_path = os.path.join(local_dir, relative)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3.download_file(bucket, key, local_path)
            count += 1
            logger.info(f"  Baixado (S3): {relative} ({obj['Size']} bytes)")

    logger.info(f"Total: {count} arquivos baixados via S3 fallback")
    return count if count > 0 else None


def update_mlmodel_run_id(model_dir, new_run_id):
    """Atualiza o run_id no arquivo MLmodel para apontar para o staging run."""
    mlmodel_path = os.path.join(model_dir, "MLmodel")
    if not os.path.exists(mlmodel_path):
        logger.warning("Arquivo MLmodel nao encontrado")
        return

    with open(mlmodel_path, "r") as f:
        mlmodel = yaml.safe_load(f)

    old_run_id = mlmodel.get("run_id", "unknown")
    mlmodel["run_id"] = new_run_id
    logger.info(f"MLmodel run_id atualizado: {old_run_id} -> {new_run_id}")

    with open(mlmodel_path, "w") as f:
        yaml.dump(mlmodel, f, default_flow_style=False, sort_keys=False)


def main():
    try:
        import mlflow
        from mlflow import MlflowClient
    except ImportError:
        logger.error("mlflow nao instalado. Execute: pip install mlflow sagemaker-mlflow")
        sys.exit(1)

    logger.info(f"MLflow version: {mlflow.__version__}")
    logger.info(f"DEV tracking server: {DEV_TRACKING_SERVER_ARN}")
    logger.info(f"STAGING tracking server: {STAGING_TRACKING_SERVER_ARN}")
    logger.info(f"Model name: {MODEL_NAME}")

    force_copy = os.environ.get("FORCE_COPY", "").lower() in ("1", "true", "yes")

    # =========================================================================
    # Passo 1: Verificar se modelo ja existe no staging (idempotente)
    # =========================================================================
    logger.info("--- Passo 1: Verificando se modelo ja existe no staging ---")
    mlflow.set_tracking_uri(STAGING_TRACKING_SERVER_ARN)
    staging_client = MlflowClient()

    try:
        registered = staging_client.get_registered_model(MODEL_NAME)
        versions = registered.latest_versions
        if versions and not force_copy:
            latest_ver = versions[0]
            try:
                existing_run = staging_client.get_run(latest_ver.run_id)
                existing_threshold = existing_run.data.metrics.get("optimal_threshold")
                logger.info(
                    f"Modelo existente: versao={latest_ver.version} "
                    f"optimal_threshold={existing_threshold}"
                )

                # Se threshold != 0.5 (hardcoded antigo) e != None, modelo valido
                if existing_threshold is not None and existing_threshold != 0.5:
                    logger.info(
                        f"Modelo '{MODEL_NAME}' ja existe no staging com "
                        f"threshold={existing_threshold} (valido). Pulando copia."
                    )
                    return

                logger.warning(
                    f"Modelo existente tem threshold={existing_threshold} "
                    f"(invalido - copia antiga com modelo errado). "
                    f"Criando nova versao com modelo correto..."
                )
            except Exception as run_err:
                logger.warning(
                    f"Nao foi possivel validar modelo existente: {run_err}. "
                    f"Recriando..."
                )
        elif force_copy:
            logger.info("FORCE_COPY habilitado - pulando check de idempotencia")
    except Exception as e:
        logger.info(f"Modelo '{MODEL_NAME}' nao encontrado no staging: {e}")
        logger.info("Iniciando copia do dev...")

    # =========================================================================
    # Passo 2: Conectar ao DEV MLflow App e buscar modelo
    # =========================================================================
    logger.info("--- Passo 2: Conectando ao DEV MLflow App ---")
    mlflow.set_tracking_uri(DEV_TRACKING_SERVER_ARN)
    dev_client = MlflowClient()

    try:
        dev_model = dev_client.get_registered_model(MODEL_NAME)
        dev_versions = dev_model.latest_versions
        if not dev_versions:
            logger.error(f"Modelo '{MODEL_NAME}' nao tem versoes no DEV")
            sys.exit(1)

        latest_version = dev_versions[0]
        dev_run_id = latest_version.run_id
        dev_version = latest_version.version
        logger.info(
            f"DEV modelo: {MODEL_NAME} version={dev_version} run_id={dev_run_id}"
        )

        # Buscar metrics e params do run
        dev_run = dev_client.get_run(dev_run_id)
        dev_metrics = dev_run.data.metrics
        dev_params = dev_run.data.params
        dev_tags = {
            k: v for k, v in dev_run.data.tags.items()
            if not k.startswith("mlflow.")
        }

        logger.info(f"DEV metrics: {dev_metrics}")
        logger.info(f"DEV params count: {len(dev_params)}")

        optimal_threshold = dev_metrics.get("optimal_threshold", "NAO ENCONTRADO")
        logger.info(f"optimal_threshold = {optimal_threshold}")

    except Exception as e:
        logger.error(f"Falha ao buscar modelo do DEV MLflow App: {e}")
        sys.exit(1)

    # =========================================================================
    # Passo 3: Baixar artifacts do modelo DEV
    # =========================================================================
    logger.info("--- Passo 3: Baixando artifacts do modelo DEV ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        model_dir = None

        # Primario: MLflow API
        try:
            logger.info(
                f"Baixando via MLflow API: models:/{MODEL_NAME}/{dev_version}"
            )
            model_dir = mlflow.artifacts.download_artifacts(
                artifact_uri=f"models:/{MODEL_NAME}/{dev_version}",
                dst_path=tmpdir
            )
            logger.info(f"Baixado para: {model_dir}")
            files = os.listdir(model_dir)
            logger.info(f"Arquivos no model_dir: {files}")

        except Exception as e:
            logger.warning(f"Download via MLflow falhou: {e}")
            logger.info("Tentando fallback via S3 direto...")

            # Fallback: S3 direto do bucket do MLflow App DEV
            model_dir = os.path.join(tmpdir, "model")
            os.makedirs(model_dir, exist_ok=True)
            result = download_model_from_s3(
                DEV_FALLBACK_BUCKET, DEV_REGION, model_dir
            )
            if result is None:
                logger.error(
                    "Download falhou tanto via MLflow quanto via S3 fallback"
                )
                sys.exit(1)
            files = os.listdir(model_dir)
            logger.info(f"Arquivos no model_dir (S3 fallback): {files}")

        # Validar arquivos essenciais
        if "MLmodel" not in files:
            logger.error("Arquivo essencial 'MLmodel' nao encontrado nos artifacts")
            sys.exit(1)

        # =====================================================================
        # Passo 4: Registrar modelo no STAGING MLflow
        # =====================================================================
        logger.info("--- Passo 4: Registrando modelo no STAGING MLflow ---")
        mlflow.set_tracking_uri(STAGING_TRACKING_SERVER_ARN)
        staging_client = MlflowClient()

        # Criar ou buscar experiment
        try:
            experiment_id = staging_client.create_experiment(EXPERIMENT_NAME)
            logger.info(
                f"Experiment criado: {EXPERIMENT_NAME} (ID={experiment_id})"
            )
        except Exception:
            experiment = staging_client.get_experiment_by_name(EXPERIMENT_NAME)
            experiment_id = experiment.experiment_id
            logger.info(
                f"Experiment existente: {EXPERIMENT_NAME} (ID={experiment_id})"
            )

        mlflow.set_experiment(EXPERIMENT_NAME)

        with mlflow.start_run(run_name="best_estimator") as run:
            staging_run_id = run.info.run_id
            logger.info(f"Staging run ID: {staging_run_id}")

            # Log TODAS as metrics do DEV
            for key, value in dev_metrics.items():
                mlflow.log_metric(key, value)
                logger.info(f"  Metric: {key} = {value}")

            # Log TODOS os params do DEV
            if dev_params:
                mlflow.log_params(dev_params)
                logger.info(f"  Logados {len(dev_params)} params")

            # Tags para rastreabilidade
            mlflow.set_tag("source", "copy-from-dev")
            mlflow.set_tag("dev_run_id", dev_run_id)
            mlflow.set_tag("dev_model_version", dev_version)
            for key, value in dev_tags.items():
                mlflow.set_tag(f"dev_{key}", value)

            # Atualizar run_id no MLmodel
            update_mlmodel_run_id(model_dir, staging_run_id)

            # Upload artifacts
            mlflow.log_artifacts(model_dir, artifact_path="model")
            logger.info("Model artifacts uploaded para staging")

        # =====================================================================
        # Passo 5: Registrar modelo no registry
        # =====================================================================
        logger.info("--- Passo 5: Registrando modelo no Model Registry ---")
        model_uri = f"runs:/{staging_run_id}/model"
        result = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
        logger.info(f"Modelo registrado: {MODEL_NAME} versao {result.version}")

    logger.info("=" * 60)
    logger.info(f"SUCESSO: Modelo '{MODEL_NAME}' copiado de DEV para STAGING")
    logger.info(f"  Staging Run ID: {staging_run_id}")
    logger.info(f"  Model Version: {result.version}")
    logger.info(f"  optimal_threshold: {dev_metrics.get('optimal_threshold', 'N/A')}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
