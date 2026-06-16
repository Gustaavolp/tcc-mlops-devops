import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler
from sklearn.compose import ColumnTransformer, make_column_selector

import boto3

def _load_and_split(df, select):

    df_flag = df[df["dataset_flag"] == select];

    y = df_flag["FLAG_FRAUD"]
    x = df_flag.drop("FLAG_FRAUD", axis = 1).drop("dataset_flag", axis = 1)

    return x, y


def get_data(path):

    print(f"Loading data from S3...")
    df = pd.read_parquet (
        path,
        engine="pyarrow",
    )
    print(f"{path} loaded.")

    x_train, y_train = _load_and_split(df, "train")
    x_test, y_test = _load_and_split(df, "test")
    x_oot, y_oot = _load_and_split(df, "oot")

    return x_train, x_test, x_oot, y_train, y_test, y_oot

def get_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("one_hot", OneHotEncoder(handle_unknown='ignore', sparse_output=True), make_column_selector(dtype_include=['object', 'bool'])),
            ('num', MinMaxScaler(), make_column_selector(dtype_include='number'))
        ],
        verbose=True
    )
