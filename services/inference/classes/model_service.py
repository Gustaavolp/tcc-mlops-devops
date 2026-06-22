import mlflow.pyfunc
import pandas as pd
import logging
import sys
from typing import Dict, Any, List

import mlflow
from mlflow.tracking import MlflowClient

class ModelService:
    def __init__(self, tracking_uri, model_name):
        mlflow.set_tracking_uri(tracking_uri)
        self.model = None
        self.tracking_uri = tracking_uri
        self.model_name = model_name
        self._load_model()

    def _load_model(self):
        """Carrega o modelo MLflow diretamente do S3."""
        try:
            logging.info(f"Carregando modelo '{self.model_name}' de: {self.tracking_uri}")
            client = MlflowClient(tracking_uri = self.tracking_uri)
            models = client.search_registered_models()

            registered_model = client.get_registered_model(name=self.model_name)
            latest_version = registered_model.latest_versions[0]
            
            self.model = mlflow.pyfunc.load_model(
                model_uri=f"models:/{self.model_name}/{latest_version.version}"
            )

            run = client.get_run(self.model.metadata.run_id)

            # Recupera o threshold
            self.threshold = run.data.metrics.get("optimal_threshold")
            if self.threshold is None:
                logging.warning(
                    "Métrica 'optimal_threshold' não encontrada. Usando threshold padrão = 0.5"
                )
                self.threshold = 0.5

            logging.info("Modelo carregado com sucesso.")
        except Exception as e:
            logging.critical(f"Erro fatal ao carregar modelo: {e}")
            sys.exit(1)

    def predict(self, processed_data_list: List[Dict[str, Any]]) -> List[float]:
        if not self.model:
            raise RuntimeError("Modelo não está carregado.")
            
        if not processed_data_list:
            logging.warning("Lista de dados vazia para predição.")
            return []

        # 1. Conversão Direta (O Transformer já garantiu o Schema)
        df_input = self._prepare_dataframe(processed_data_list)
        
        # 2. Inferência
        try:
            predictions = self.model.predict(df_input)
            
            # Normaliza saída para lista de floats
            if hasattr(predictions, 'tolist'):
                return predictions.tolist()
            return list(predictions)
            
        except Exception as e:
            logging.error(f"Erro durante .predict(): {e}")
            # Retorna 0.0 (seguro) para cada item em caso de falha
            return [0.0] * len(processed_data_list)
    
    def predict_proba(self, processed_data_list: List[Dict[str, Any]]) -> List[Any]:
        if not self.model:
            raise RuntimeError("Modelo não está carregado.")

        if not processed_data_list:
            logging.warning("Lista de dados vazia para predição.")
            return []

        df_input = self._prepare_dataframe(processed_data_list)

        try:
            # Tentativa 1: modelo sklearn/xgboost encapsulado no pyfunc
            if hasattr(self.model, "_model_impl") and hasattr(self.model._model_impl, "predict_proba"):
                probabilities = self.model._model_impl.predict_proba(df_input)

            # Tentativa 2: pyfunc expondo predict_proba diretamente
            elif hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(df_input)

            else:
                raise AttributeError("Modelo não suporta predict_proba()")

            if hasattr(probabilities, "tolist"):
                return probabilities.tolist()

            return list(probabilities)

        except Exception as e:
            logging.error(f"Erro durante predict_proba(): {e}")
            # Retorno seguro: probabilidades zeradas
            return [[0.0, 0.0]] * len(processed_data_list)

    def _prepare_dataframe(self, payload_list: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converte lista de dicts em DataFrame.
        Assume que o Transformer já fez a limpeza e tipagem.
        """
        # Cria DataFrame direto da lista de dicionários
        df = pd.DataFrame(payload_list)

        # Ajuste Fino: Datas para MLflow
        # O MLflow pode ser chato com objetos datetime python puros misturados
        # Garantimos que colunas de data sejam datetime64[ns]
        date_cols = ["PURCHASE_DATE_AND_TIME"]
        
        for col in date_cols:
            if col in df.columns:
                # errors='coerce' transforma erros em NaT (Not a Time) sem quebrar
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df