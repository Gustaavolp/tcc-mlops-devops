import os
import logging

from sagemaker.modules.train import ModelTrainer
from sagemaker.modules.configs import Compute
from sagemaker.modules.configs import StoppingCondition

from itertools import product


# ---------------------------
# Logging
# ---------------------------
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


# ---------------------------
# Configuracoes via env vars
# ---------------------------
MLFLOW_URI = os.environ.get("MLFLOW_URI")
MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME", "classificacao_6.0.0")
SAGEMAKER_ROLE = os.environ.get("SAGEMAKER_ROLE")
TRAINING_IMAGE = os.environ.get("TRAINING_IMAGE")
DATA_S3_PATH = os.environ.get("DATA_S3_PATH")
DATASET_NAME = os.environ.get("DATASET_NAME", "gold")
IS_PROD = os.environ.get("IS_PROD", "False")
INSTANCE_TYPE = os.environ.get("INSTANCE_TYPE", "ml.r5.4xlarge")


models = [
    "XGBClassifier",
    # "LogisticRegression",
    # "KNeighborsClassifier",
    # "MultinomialNB",
    # "SVC_linear",
    # "SVC_rbf",
    # "RandomForestClassifier",
    # "SGDClassifier"
]

imputers = [
    "SimpleImputer",
    # "KNNImputer",
]

reducoes = [
    # "SVD",
    # "PCA",
    "NoApply",
]

imbalances = [
    "SMOTE",
    # "ADASYN",
    # "RandomUnderSampler",
    # "ENN",
    # "TomekLinks",
    # "SMOTEENN",
    # "NoApply",
]


# ---------------------------
# Lambda handler
# ---------------------------
def lambda_handler(event, context):
    logger.info("Training launcher invoked")

    jobs_launched = []

    for model_name, imputer_name, reduction_name, imbalance_name in product(models, imputers, reducoes, imbalances):

        hyperparameters = {
            "mlflow_uri": MLFLOW_URI,
            "mlflow_experiment_name": MLFLOW_EXPERIMENT_NAME,
            "model_name": model_name,
            "imputer_name": imputer_name,
            "reduction_name": reduction_name,
            "imbalance_name": imbalance_name,
            "dataset_name": DATASET_NAME,
            "path_s3_data": DATA_S3_PATH,
            "is_prod": IS_PROD,
        }

        logger.info("Launching training job: %s", hyperparameters)

        model_trainer = ModelTrainer(
            role=SAGEMAKER_ROLE,
            training_image=TRAINING_IMAGE,
            hyperparameters=hyperparameters,
            stopping_condition=StoppingCondition(
                max_runtime_in_seconds=3600 * 72,
            ),
            compute=Compute(
                instance_type=INSTANCE_TYPE,
                instance_count=1,
            ),
        )

        model_trainer.train(wait=False)

        job_name = f"{model_name}_{imputer_name}_{reduction_name}_{imbalance_name}"
        jobs_launched.append(job_name)
        logger.info("Job launched: %s", job_name)

    logger.info("Total jobs launched: %d", len(jobs_launched))

    return {
        "statusCode": 200,
        "jobs_launched": jobs_launched,
        "total_jobs": len(jobs_launched),
    }


if __name__ == "__main__":
    print(lambda_handler({}, None))
