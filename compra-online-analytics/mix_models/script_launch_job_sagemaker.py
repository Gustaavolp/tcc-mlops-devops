## imports para v3
# import sagemaker
# from sagemaker.train import ModelTrainer
# from sagemaker.core.resources import StoppingCondition

from sagemaker.modules.train import ModelTrainer
from sagemaker.modules.configs import Compute
from sagemaker.modules.configs import StoppingCondition


from itertools import product


models = [
     "XGBClassifier",
     # "LogisticRegression",
     # "KNeighborsClassifier",
     # MultinomialNB",
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
   # "MiniBatchSparsePCA",
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

for model_name, imputer_name, reduction_name, imbalance_name in product(models, imputers, reducoes, imbalances):


    hyperparameters = {
        "mlflow_uri": "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ",
        # "mlflow_uri": "arn:aws:sagemaker:sa-east-1:888577064416:mlflow-app/app-745OOZVUK6XJ",
        "mlflow_experiment_name": "classificacao__1.0.5",
        "model_name": model_name,
        "imputer_name": imputer_name,
        "reduction_name": reduction_name,
        "imbalance_name": imbalance_name,

        "dataset_name": "gold", 

        # "path_s3_data" : "s3://elo-fraud-data-processed-dev-888577064416/training_zone/silver.parquet",
        "path_s3_data" : "s3://elo-fraud-data-processed-dev-888577064416/training_zone/gold.parquet",
        "is_prod" : "True"


    }

    model_trainer = ModelTrainer (
        role = "arn:aws:iam::888577064416:role/elo-fraud-mlflow-dev-execution-role",
        # role = "arn:aws:iam::888577064416:role/elo-fraud-mlflow-stg-execution-role",
        training_image="888577064416.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-model-dev:latest",
        # training_image="888577064416.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-model-staging:latest",
        hyperparameters=hyperparameters,
        stopping_condition = StoppingCondition(
                max_runtime_in_seconds=3600*72, 
        ),
        compute = Compute(
            instance_type="ml.r5.4xlarge",
            instance_count=1
        ),
    )

    model_trainer.train (
            wait = True,
    )
