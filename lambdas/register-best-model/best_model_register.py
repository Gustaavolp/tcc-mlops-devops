import os
import json
import mlflow
import logging

import boto3
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

from envs import Envs
from utils import Utils

# Set MLflow logging level to ERROR to reduce verbosity
logging.getLogger("mlflow").setLevel(logging.ERROR)
logging.getLogger("mlflow.tracking").setLevel(logging.ERROR)
logging.getLogger("mlflow.store").setLevel(logging.ERROR)
logging.getLogger("mlflow.store.model_registry").setLevel(logging.ERROR)

class MlflowModelRegistry:

    @Utils.log_errors
    def __init__(self):

        # Name for the model in the registry tab
        self.MODEL_NAME = Envs.MODEL_NAME
        self.METRIC_TO_COMPARE = Envs.METRIC_TO_COMPARE
        self.MLFLOW_TRACKING_URI = Envs.MLFLOW_TRACKING_URI
        self.MLFLOW_BEST_MODEL_RUN = Envs.MLFLOW_BEST_MODEL_RUN
        self.MLFLOW_TARGET_TAG_KEY = Envs.MLFLOW_TARGET_TAG_KEY
        self.MLFLOW_TARGET_TAG = Envs.MLFLOW_TARGET_TAG

        # Disable MLflow HTTP retries
        os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = "3"
        os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = "20"
        os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "false"

    def publish_promotion_event(self, version, run_id, metric):
        """
        Publica no EventBridge o evento de nova versão registrada, que dispara o
        rolling restart do serviço de inferência no mesmo ambiente.
        Falhas aqui não desfazem o registro: são logadas e retornam False.
        """
        if not Envs.PUBLISH_PROMOTION_EVENT:
            return False

        detail = {
            "model_name": self.MODEL_NAME,
            "version": str(version) if version is not None else None,
            "run_id": run_id,
            "metric": self.METRIC_TO_COMPARE,
            "metric_value": float(metric) if metric is not None else None,
            "environment": Envs.ENVIRONMENT
        }

        try:
            response = boto3.client("events").put_events(Entries = [{
                "Source": Envs.PROMOTION_EVENT_SOURCE,
                "DetailType": "ModelVersionRegistered",
                "Detail": json.dumps(detail),
                "EventBusName": Envs.PROMOTION_EVENT_BUS
            }])
            if response.get("FailedEntryCount", 0):
                logging.error(f"Evento de promoção rejeitado: {response.get('Entries')}")
                return False
            logging.info(f"Evento de promoção publicado: {detail}")
            return True
        except Exception as e:
            logging.error(f"Falha ao publicar evento de promoção: {e}")
            return False

    @Utils.log_errors
    def register_best_model(self):
        """
        Register the best model from the latest production experiment
        if its metric is better than the currently registered model.
        1. Fetch the latest production experiment.
        2. Identify the best run based on the specified metric.
        3. Compare the metric with the registered model's metric.
        4. Register the new model if it outperforms the existing one.
        5. Handle exceptions for robustness.
        6. Log relevant information and errors.
        """

        try:

            mlflow.set_tracking_uri(self.MLFLOW_TRACKING_URI)

            client = MlflowClient(tracking_uri = self.MLFLOW_TRACKING_URI)

            # Get the most recently updated experiment
            latest_experiment = client.search_experiments(
                order_by = ["last_update_time DESC"],
                filter_string = f"tags.{self.MLFLOW_TARGET_TAG_KEY} LIKE '%{self.MLFLOW_TARGET_TAG}%'",
                max_results = 1
            )

            latest_experiment = list(latest_experiment)

            if latest_experiment == []:

                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "No prods experiments found."})
                }

            experiment_id = latest_experiment[0].experiment_id

            # Search for the best run in the experiment based on the specified metric
            candidate_runs = mlflow.search_runs(
                experiment_ids = [experiment_id],
                order_by = [f"{self.METRIC_TO_COMPARE} DESC"],
                max_results = 1
            )

            if candidate_runs.empty:

                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "No runs found in the experiment."})
                }

            # Get the information from the best candidate run
            best_candidate_run = candidate_runs.iloc[0]
            candidate_metric = best_candidate_run[self.METRIC_TO_COMPARE]
            candidate_run_id = best_candidate_run.run_id

        except Exception as e:

            return {
                "statusCode": 500,
                "body": json.dumps({"message": f"Error fetching experiment or runs: {e}"})
            }

        should_register_model = False

        try:

            # Try to get the registered model
            registered_model = client.get_registered_model(name = self.MODEL_NAME)

            # Check if there are any versions
            if not registered_model.latest_versions:

                should_register_model = True

            else:

                latest_version = registered_model.latest_versions[0]

                # Get the metric of the registered model run
                registered_run = client.get_run(latest_version.run_id)
                registered_metric = registered_run.data.metrics.get(self.METRIC_TO_COMPARE.replace("metrics.", ""), 0)

                # Compare metrics
                if candidate_metric > registered_metric:

                    should_register_model = True

        except MlflowException as e:

            # If the model is not found (RESOURCE_DOES_NOT_EXIST), it should be registered
            if "RESOURCE_DOES_NOT_EXIST" in str(e):

                should_register_model = True

            else:

                return {
                    "statusCode": 500,
                    "body": json.dumps({"message": f"Error accessing registered model: {e}"})
                }

        # Register the model if it is better, or if no model exists or has no versions
        if should_register_model:

            try:

                model_uri = f"runs:/{candidate_run_id}/{self.MLFLOW_BEST_MODEL_RUN}"

                model_version = mlflow.register_model(
                    model_uri = model_uri,
                    name = self.MODEL_NAME
                )

                event_published = self.publish_promotion_event(
                    version = getattr(model_version, "version", None),
                    run_id = candidate_run_id,
                    metric = candidate_metric
                )

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "message": "Model registered successfully.",
                        "version": str(getattr(model_version, "version", "")),
                        "event_published": event_published
                    })
                }

            except Exception as e:

                return {
                    "statusCode": 500,
                    "body": json.dumps({"message": f"Error registering model: {e}"})
                }

        else:

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No model is eligible for registration."})
            }
