# Models

Esse código treina diferentes modelos utilizando *grid search* com *cross-validation* e *TunedThresholdClassifierCV*.  
Adicione novos modelos ou ajuste os hiperparâmetros em `src/models/models.py`.

## Como treinar localmente

```bash
docker build -t sagemaker_job_train .
```

```bash
docker run -d \
    -p 5000:5000 \
    -v $(pwd)/mlflow_data:/mlflow \
    ghcr.io/mlflow/mlflow \
    mlflow server\
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri sqlite:////mlflow/mlflow.db \
    --default-artifact-root file:///mlflow/artifacts
```

```bash
docker run --rm \
  --network=host \
  sagemaker_job_train \
  python train.py \
  --mlflow_uri "http://127.0.0.1:5000" \
  --mlflow_experiment_name "classificacao_local" \
  --imputer_name "SimpleImputer" \
  --reduction_name "NoApply" \
  --imbalance_name "SMOTE" \
  --dataset_name "gold" \
  --model_name "XGBClassifier" \
  --path_s3_data "s3://elo-fraud-data-processed-staging-888577064416/training_zone/gold_20260102.parquet" \
  --is_prod "True"
  ```


### Referência de Parâmetros de Treinamento

| Categoria | Parâmetro CLI | Valores Disponíveis |
| :---          | :---               | :--- |
| **Modelos**   | `--model_name`     | `XGBClassifier`, `LogisticRegression` |
| **Imputação** | `--imputer_name`   | `SimpleImputer`, `KNNImputer` |
| **Redução**   | `--reduction_name` | `NoApply`, `SVD`, `PCA` |
| **Balanço**   | `--imbalance_name` |  `NoApply`, `SMOTE`, `ADASYN`, `RandomUnderSampler`, `ENN`, `TomekLinks`, `SMOTEENN` |
| **Dataset**   | `--dataset_name`   | `gold`, `sample` |
| **Ambiente** | `--is_prod` | `True`, `False` |

## Como treinar no sagemaker

Primeiro, realize o build e o push da sua imagem Docker para o Amazon ECR (Elastic Container Registry). Após, disponibilizar a imagem no ECR, execute o código abaixo e instaciar o job de treinamento no SageMaker.

```bash
 python script_launch_job_sagemaker.py
```
