from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB;
from sklearn.ensemble import  RandomForestClassifier

from sklearn.impute import SimpleImputer, KNNImputer

from sklearn.decomposition import TruncatedSVD, PCA, MiniBatchSparsePCA

# from sklearn.pipeline import Pipeline
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler, EditedNearestNeighbours, TomekLinks
from imblearn.combine import SMOTEENN

from dataloader.dataloader import get_preprocessor

from scikeras.wrappers import KerasClassifier
from models.NN import build_model


from xgboost import XGBClassifier

from imblearn.combine import SMOTEENN

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
                 'clf__n_estimators': [300, 350],
                 'clf__learning_rate': [0.3, 0.4],
                 'clf__max_depth': [11],
                 'clf__objective': ['binary:logistic'],
                 # 'clf__scale_pos_weight' : [88931/413],
                 }
             ),

            "LogisticRegression": (
                LogisticRegression(),
                {
                    'clf__C': [0.01, 0.1, 1.0, 10.0],
                    'clf__penalty': ['l1', 'l2'],
                    'clf__solver': ['saga'], 
                    'clf__class_weight': [None, 'balanced'], 
                    'clf__l1_ratio': [0.5] 
                }
            ),

        }

        self.imputer_dict = {
            "SimpleImputer": (
                SimpleImputer(),
                {
                    'imputer__strategy': ['median'],
                }
            ),
            "KNNImputer": (
                KNNImputer(),
                {
                    'imputer__n_neighbors': [3, 5, 11],
                    'imputer__weights': ['uniform', 'distance']
                }
            ),

        }

        self.data_reduction_dict = {
            "SVD" : (
                TruncatedSVD(random_state=42),
                {
                'data_reduction__n_components': [50, 60, 100], 
                'data_reduction__algorithm': ['randomized', 'arpack'] 
                }
            ),

            "PCA": (
                PCA(random_state=42),
                {
                    'data_reduction__n_components': ['mle' ,0.95, 0.99], 
                    'data_reduction__svd_solver': ['full',]
                }
            ),

            "MiniBatchSparsePCA": (
                MiniBatchSparsePCA(),
                {
                    'data_reduction__n_components': [10, 20],
                    'data_reduction__batch_size': [1000, 5000],
                    'data_reduction__alpha': [1, 5],
                }
            ),

            "NoApply": (None, {})
        }

        self.imbalance = {

           # Over-sampling methods
            "SMOTE" : (
                SMOTE(random_state=42),
                {
                    'imbalance__k_neighbors': [3],
                }
            ),
            "ADASYN": (
                ADASYN(random_state=42),
                {
                    'imbalance__n_neighbors': [3, 5],
                }
            ),

            # Under-sampling methods
            "RandomUnderSampler": (
                RandomUnderSampler(random_state=42),
                {
                    'imbalance__sampling_strategy': ['auto', 'majority']
                }
            ),

            "ENN": (
                    EditedNearestNeighbours(),
                    {
                        'imbalance__n_neighbors': [3, 5],
                        'imbalance__kind_sel': ['all', 'mode']
                    }
            ),

            "TomekLinks": (
                TomekLinks(),
                {}
            ),

            # combine
            "SMOTEENN": (
                SMOTEENN(
                    smote=SMOTE(random_state=42), 
                    enn=EditedNearestNeighbours(), 
                    random_state=42
                ),
                {
                    'imbalance__smote__k_neighbors': [3, 5],
                    'imbalance__enn__n_neighbors': [3]
                }       
            ),

            "NoApply": (None, {})
        }


    def get_grid_search(self, model_name, imputer_name, reduction_name, imbalance_name):

        model, param_model = self.models_dict[model_name]

        imputer, param_imputer = self.imputer_dict[imputer_name]

        data_reduction, param_data_reduction = self.data_reduction_dict[reduction_name]

        imbalance, param_imbalance = self.imbalance[imbalance_name]
        
        pipeline = Pipeline([
            ('preprocessor', get_preprocessor()),
            ('imputer', imputer),
            ('data_reduction', data_reduction),
            ('imbalance', imbalance),
            ('clf', model)
        ])

        combined_param_grid = {
            **param_imputer,
            **param_imbalance,
            **param_data_reduction,
            **param_model,
        }

        to_remove = []
        if reduction_name == 'NoApply':
            to_remove.append('data_reduction')
        if imbalance_name == 'NoApply':
            to_remove.append('imbalance')

        pipeline.steps = [step for step in pipeline.steps if step[0] not in to_remove]


        grid_search = GridSearchCV(
                pipeline,
                combined_param_grid,
                n_jobs = -1,
                cv= 5,
                scoring='balanced_accuracy',
                verbose = 3,
                error_score = "raise",
        )


        return grid_search
