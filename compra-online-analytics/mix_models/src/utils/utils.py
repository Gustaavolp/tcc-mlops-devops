import matplotlib.pyplot as plt
import numpy as np
import itertools

import mlflow

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, balanced_accuracy_score, recall_score, precision_score

import os

class Logs:

    def __init__(self, path='./res/'):
            self.path = path
            os.makedirs(self.path)

    def create_confusion_matrix(self, cm, classes, normalize=False, title='Confusion matrix', file_name = 'Confusion_Matrix.png'):
        """
        This function prints and plots the confusion matrix.
        Normalization can be applied by setting `normalize=True`.
        """

        plt.figure(figsize=(10, 7))
        plt.imshow(cm, interpolation='nearest', cmap = 'Blues')
        plt.title(title)
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)

        if normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        thresh = cm.max() / 2.
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
            plt.text(j, i, cm[i, j],
                horizontalalignment="center",
                color="white" if cm[i, j] > thresh else "black")

        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
          
        plt.savefig(self.path + file_name)
        plt.close()


    def create_file(self, content, file_name):
        with open(self.path + file_name, 'w') as f:
            f.write(content)


    def saving_different_scores(self, clf, x_test, y_test, file_name='different_scores.csv'):
        rows = []

        proba = clf.predict_proba(x_test)[:, 1]*1000

        for threshold in range(1, 1000):

            y_pred = (proba > threshold).astype(int)

            tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
            balanced_accuracy = balanced_accuracy_score(y_test, y_pred)
            fpr = fp /(fp + tn) if fn + tn != 0 else 0;
            recall = recall_score(y_test, y_pred, zero_division = 0)
            precision = precision_score(y_test, y_pred, zero_division = 0)
            taxa_de_alerta = y_pred.mean()
            

            rows.append ({
                "threshold": threshold,
                "TN": tn,
                "FP": fp,
                "FN": fn,
                "TP": tp,
                "balanced_accuracy_score": balanced_accuracy,
                "FPR": fpr,
                "recall": recall,
                "precision": precision,
                "taxa_de_alerta (PPR)": taxa_de_alerta,
            })

        df = pd.DataFrame(rows)

        df.to_csv(self.path + file_name, index=False)


    def create_logs(self, clf, x_test, y_test, sufix_name_files):
        y_pred = clf.predict(x_test)

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

        nomes = ['valido', 'fraude'];

        self.create_file(str(classification_report(y_test, y_pred, target_names=nomes)), "classification_report_"+sufix_name_files+".txt")
        self.create_confusion_matrix(confusion_matrix(y_test, y_pred), nomes, file_name = "Confusion_Matrix_"+sufix_name_files+".png")
        self.saving_different_scores(clf, x_test, y_test, file_name="different_scores_"+sufix_name_files+".csv")

        mlflow.log_metric("ppr_" + sufix_name_files, y_pred.mean())
        mlflow.log_metric("balanced_accuracy_" + sufix_name_files, balanced_accuracy_score(y_test, y_pred))
        mlflow.log_metric("recall_" + sufix_name_files, recall_score(y_test, y_pred, zero_division = 0))
        mlflow.log_metric("precision_" + sufix_name_files, precision_score(y_test, y_pred, zero_division = 0))
        mlflow.log_metric("fpr_" + sufix_name_files, fp /(fp + tn) if fn + tn != 0 else 0)

    def create_grath_for_importance_feature(self, clf, file_name):
        df = pd.DataFrame({
            'Feature': clf.estimator_.named_steps['preprocessor'].get_feature_names_out(), 
            'Feature importance': clf.estimator_.named_steps['clf'].feature_importances_
        }).sort_values(by='Feature importance', ascending=False)
        
        df.to_csv(self.path + file_name + ".csv", index=False)

    def  log_tuned_threshold(self, clf):

        tuning_results = pd.DataFrame({
            "threshold": clf.cv_results_["thresholds"],
            "score": clf.cv_results_["scores"]
        })

        mlflow.log_metric("optimal_threshold", clf.best_threshold_)
        tuning_results.to_csv(self.path+"threshold_tuning_curve.csv", index=False)

    def save_all_files_created_in_mlflow(self):
        mlflow.log_artifacts(self.path)

