from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE

from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB;
from sklearn.ensemble import  RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from scikeras.wrappers import KerasClassifier

from xgboost import XGBClassifier

from models.NN import build_model

from dataloader.dataloader import get_preprocessor

class Models:
    def __init__(self):
        self.models_dict = {
          "NN_LSTM": (
                KerasClassifier(
                    model=build_model,
                    optimizer="adam",
                    loss="binary_crossentropy",
                    metrics=["accuracy"],
                    epochs=20, 
                    batch_size=32,
                    verbose=0,
                ),
                {
                    'clf__model__lstm_units': [
                        [50], 
                        [100],
                        [64, 32],
                        [124, 64, 32]
                    ],
                     'clf__model__dropout': [0.1, 0.3],
                }
            ),
          "XGBClassifier": (
                XGBClassifier(), {
                'clf__n_estimators': [50, 100, 200, 300],
                'clf__learning_rate': [0.001, 0.01, 0.1, 0.3],
                'clf__max_depth': [3, 6, 9],
                'clf__objective': ['binary:logistic'],
                }
            ),
            "LogisticRegression": (
                LogisticRegression(),
                {'clf__C': [10**x for x in range(-2, 4)], 'clf__penalty': ['l1', 'l2']}
            ),
            "SVC_linear": (
                SVC(kernel='linear'),
                {'clf__C': [10**x for x in range(-2, 4)]}
            ),
            "SVC_rbf": (
                SVC(kernel='rbf'),
                {'clf__C': [10**x for x in range(-2, 4)], 'clf__gamma': ['scale', 'auto']}
            ),
            "KNeighborsClassifier": (
                KNeighborsClassifier(),
                {'clf__n_neighbors': [1, 3, 5, 7, 9, 11]}
            ),
            "MultinomialNB": (
                MultinomialNB(),
                {'clf__alpha': [1, 0.1, 0.01, 1e-3, 1e-4]}
            ),
            "RandomForestClassifier": (
                RandomForestClassifier(),
                {'clf__n_estimators': [10, 50, 100], 'clf__max_features': ['auto', 'sqrt', 'log2']}
            ),
            "SGDClassifier": (
                SGDClassifier(),
                {'clf__alpha': [0.0001, 0.001, 0.01, 0.1, 1]}
            ),
        }


    def selected_models(self):

        select_dict = list(self.models_dict.keys())

        print("\nselecione os modelos\n")

        for (i, name) in enumerate(select_dict):
            print(f"{i:^2} {name}")

        return [select_dict[name] for name in map(int, input("Digite os números dos modelos que deseja treinar (separados por espaço): ").split())]


    def get_grid_search(self):

        models = []

        for name in self.selected_models():

            model, param_grid = self.models_dict[name]

            pipeline = Pipeline([
                ('preprocessor', get_preprocessor()),
                ('SMOTE', SMOTE()),
                ('clf', model)
            ])

            combined_param_grid = {
                **param_grid
            }

            grid_search = GridSearchCV(pipeline, combined_param_grid, n_jobs = -1, cv= 5)

            models.append((name, grid_search))

        return models

