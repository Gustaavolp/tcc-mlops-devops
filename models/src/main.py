from dataloader.dataloader import get_data
from models.models import Models
from utils.utils import save_confusion_matrix

from sklearn.metrics import classification_report, confusion_matrix

import os

import mlflow


mlflow.set_tracking_uri(uri= "http://localhost:5000/")
mlflow.set_experiment("classificacao_1.0.0")


def run(data, name_dataset):

    x_train, x_test, y_train, y_test, nomes = data;


    print("Nomes das classes:", nomes)

## carregando modelos
    print("carregando modelos")
    models = Models();

    mlflow.autolog()

    for name, clf in models.get_grid_search():


        print ("-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.")

        with mlflow.start_run(run_name = name):
            print ("treinando " + name)
            clf.fit(x_train, y_train);

            predictions = clf.predict(x_test)

            report = classification_report(y_test, predictions, target_names=nomes)
            conf_matrix = confusion_matrix(y_test, predictions )
            

            print("report")
            print(report)

            print("best params")
            print(clf.best_params_)

            print("conf_matrix")
            print(conf_matrix)


            path = './res/' + name_dataset + '/' + name + '/';
            if not os.path.exists(path):
                os.makedirs(path)


            with open (path + "classification_report.txt", 'w') as f:
                f.write(str(report))

            save_confusion_matrix(path, conf_matrix, nomes)

            with open(path + "params" + '.txt', 'w') as f:
                f.write(str(clf.best_params_))


            mlflow.log_artifacts(path)

run(get_data(), "sample")
