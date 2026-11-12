"""Testes da imagem de treinamento: carga dos conjuntos e montagem do pipeline de busca."""
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GridSearchCV

from dataloader.dataloader import _load_and_split, get_data, get_preprocessor


@pytest.fixture
def frame():
    flags = ["train"] * 4 + ["test"] * 2 + ["oot"] * 2
    return pd.DataFrame({
        "AMOUNT": np.arange(8, dtype=float),
        "CURRENCY": ["986", "840"] * 4,
        "FLAG_FRAUD": [False, True] * 4,
        "dataset_flag": flags,
    })


def test_separa_conjunto_e_remove_alvo_e_flag(frame):
    x, y = _load_and_split(frame, "test")
    assert len(x) == len(y) == 2
    assert "FLAG_FRAUD" not in x.columns and "dataset_flag" not in x.columns


def test_get_data_le_parquet_e_retorna_os_tres_conjuntos(frame, tmp_path):
    path = tmp_path / "transactions.parquet"
    frame.to_parquet(path)
    x_train, x_test, x_oot, y_train, y_test, y_oot = get_data(str(path))
    assert (len(x_train), len(x_test), len(x_oot)) == (4, 2, 2)
    assert len(y_train) == 4


def test_preprocessador_codifica_categoricas_e_escala_numericas(frame):
    x, _ = _load_and_split(frame, "train")
    out = get_preprocessor().fit_transform(x)
    # 1 coluna numérica (escalada para [0, 1]) + 2 categorias de moeda (one-hot)
    assert out.shape == (4, 3)
    assert out.min() >= 0 and out.max() <= 1


def test_grid_search_xgboost_com_smote_sem_reducao():
    from models.models import Models

    grid = Models().get_grid_search("XGBClassifier", "SimpleImputer", "NoApply", "SMOTE")
    assert isinstance(grid, GridSearchCV)
    steps = [name for name, _ in grid.estimator.steps]
    assert steps == ["preprocessor", "imputer", "imbalance", "clf"]   # 'data_reduction' removida
    assert grid.scoring == "balanced_accuracy"
    assert "clf__n_estimators" in grid.param_grid
