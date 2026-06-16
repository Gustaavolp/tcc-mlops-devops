import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

def get_data():
    df = pd.read_csv("./src/../../bases_de_dados/sintetica/dataset_sintetico.csv")

    y = df['fraud_label']
    x = df.drop('fraud_label', axis=1)


    x_train, x_test, y_train, y_test  = train_test_split(x, y, test_size=0.3, random_state=42, stratify=y)

    nomes = ['valido', 'fraude'];

    return x_train, x_test, y_train, y_test, nomes


def get_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("one_hot", OneHotEncoder() , ['productType']),
            ('num', StandardScaler(), ['browserScreenHeight']),
            # ('keep_numeric', 'passthrough', ['num_col']) 
        ],
        remainder='drop' # 
    )
