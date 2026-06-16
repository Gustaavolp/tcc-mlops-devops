import argparse

from dataloader.dataloader import get_data
from models.models import Models
from utils.utils import Logs

from sklearn.model_selection import TunedThresholdClassifierCV
from sklearn.metrics import make_scorer

import mlflow
from mlflow.sklearn import log_model
import numpy as np


def run(data, name_dataset, model_name, imputer_name, reduction_name, imbalance_name, params = None):

    x_train, x_test, x_oot, y_train, y_test, y_oot = data

## carregando modelos
    print("construindo modelo")
    models = Models();

    mlflow.autolog(log_model_signatures=True)

    clf = models.get_grid_search(model_name, imputer_name, reduction_name, imbalance_name)

    print ("-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.")

    logs = Logs()

    with mlflow.start_run(run_name = " ".join([model_name, imputer_name, reduction_name, imbalance_name])):
        print("train " + " ".join([model_name, imputer_name, reduction_name, imbalance_name]))
        clf.fit(x_train, y_train);
        logs.create_file(str(clf.best_params_), "best_params.txt")

        mlflow.log_param("n_features_post_preprocessing", len(clf.best_estimator_.named_steps['preprocessor'].get_feature_names_out()))
        mlflow.log_param("n_features_post_after_preprocessing", len(x_test.columns))
        logs.create_file("\n".join([str(aux) for aux in clf.best_estimator_.named_steps['preprocessor'].transformers_]),"preprocessor_transformers.txt")

        print("start TunedThresholdClassifierCV")
        clf = TunedThresholdClassifierCV(
            estimator=clf.best_estimator_,
            scoring = make_scorer(
                lambda y_true, y_pred: (
                     -abs(y_pred.mean() - 0.02)
                ),
                response_method="predict"
            ),
            n_jobs = -1,
            cv="prefit",
            refit=False,
            thresholds = np.linspace(0.01, 1, 5000),
            store_cv_results=True,
        ).fit(x_test, y_test)

        log_model (clf, input_example=x_train[:10])

        logs.log_tuned_threshold(clf)

        logs.create_logs(clf, x_test, y_test, "teste")
        logs.create_logs(clf, x_oot, y_oot, "oot")
            
        if model_name == "XGBClassifier":
            logs.create_grath_for_importance_feature(clf, "importance_feature")

        logs.save_all_files_created_in_mlflow()

        if params != None:
            mlflow.log_params(params)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mlflow_uri", type=str, required=True)
    parser.add_argument("--mlflow_experiment_name", type=str, required=True)
    parser.add_argument("--dataset_name", type=str, required = True)

    parser.add_argument("--model_name", type=str, required = True)
    parser.add_argument("--imputer_name", type=str, required = True)
    parser.add_argument("--reduction_name", type=str, required = True)
    parser.add_argument("--imbalance_name", type=str, required = True)

    parser.add_argument("--path_s3_data", type=str, required = True)

    parser.add_argument("--is_prod", type=str, required = True)

    args = parser.parse_args()

    print("Connecting to MLflow...")
    mlflow.set_tracking_uri(uri= args.mlflow_uri)
    print("Successfully connected to MLflow.")

    mlflow.set_experiment(args.mlflow_experiment_name)

    if bool(args.is_prod):
        mlflow.set_experiment_tag(key="stage", value="prod")

    run(get_data(args.path_s3_data), args.dataset_name, args.model_name, args.imputer_name, args.reduction_name, args.imbalance_name, vars(args))

if __name__ == "__main__":
    main();
