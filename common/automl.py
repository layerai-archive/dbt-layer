from abc import abstractmethod
from typing import Any, List

import pandas as pd
from layer.decorators import model


class AutoMLModel:

    score = None
    model = None

    def __init__(self, model_type):
        self.model_type = model_type

    @abstractmethod
    def train(self, X_train, y_train, X_test, y_test, X_val, y_val, features: List[str], target: str) -> Any:
        """

        :return:
        """

    def compare_score(self, score: float) -> bool:
        """

        :return:
        """


class AutoSKLearnClassifierModel(AutoMLModel):
    def __init__(self):
        super(AutoSKLearnClassifierModel, self).__init__("classifier")

    def train(self, X_train, y_train, X_test, y_test, X_val, y_val, features: List[str], target: str):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import roc_auc_score

        model = RandomForestClassifier()
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        model_accuracy = roc_auc_score(y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class AutoXGBoostClassifierModel(AutoMLModel):
    def __init__(self):
        super(AutoXGBoostClassifierModel, self).__init__("classifier")

    def train(self, X_train, y_train, X_test, y_test, X_val, y_val, features: List[str], target: str):
        from sklearn.metrics import roc_auc_score
        from xgboost import XGBClassifier

        model = XGBClassifier(max_depth=5, learning_rate=0.1, subsample=0.5, n_estimators=10000, n_jobs=-1)
        model.fit(
            X_train, y_train, verbose=100, early_stopping_rounds=100, eval_set=[(X_train, y_train), (X_val, y_val)]
        )
        ypred_test = model.predict(X_test)
        self.score = roc_auc_score(y_test, ypred_test)
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class AutoML:

    automl_models = [AutoSKLearnClassifierModel(), AutoXGBoostClassifierModel()]

    def __init__(self, model_type: str, df: pd.DataFrame, features: List[str], target: str):
        self.model_type = model_type
        self.df = df
        self.features = features
        self.target = target
        self.score = None

    def train(self, project_name, model_name):
        print(project_name, model_name)
        X = self.df.drop([self.target], axis=1)
        y = self.df[self.target]

        # Prepare train, test and validation datasets
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30)
        X_test, X_val, y_test, y_val = train_test_split(X_test, y_test, test_size=0.5)

        # Run all models matches the requested model type
        best_model = None
        best_score = None
        for model in self.automl_models:
            if model.model_type == self.model_type:
                model.train(X_train, y_train, X_test, y_test, X_val, y_val, self.features, self.target)
                print("COMPLETE ", model, model.score)
                if best_model is None or (best_score is not None and model.compare_score(best_score)):
                    best_model = model
        if best_model is None:
            raise Exception(f"Model type '{self.model_type}' not supported yet!")
        else:
            print("BEST MODEL ", best_model, best_score)
