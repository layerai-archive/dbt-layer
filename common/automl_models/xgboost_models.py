from sklearn.metrics import accuracy_score  # type: ignore
from sklearn.model_selection import GridSearchCV  # type: ignore
from xgboost import XGBClassifier

import layer

from .base_model import AutoMLModel, TrainDataset


class XGBoostClassifier(AutoMLModel):
    name = "XGBoost Classifier"
    model_type = AutoMLModel.CLASSIFIER

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        hyperparameter_grid = {
            "max_depth": [2, 6, 10],
            "n_estimators": [60, 200],
            "learning_rate": [0.1, 0.01],
        }

        layer.log({"xgboost hyperparameter grid": hyperparameter_grid})

        estimator = XGBClassifier(seed=42, eval_metric="mlogloss", use_label_encoder=False)
        self.model: GridSearchCV = GridSearchCV(
            estimator=estimator, param_grid=hyperparameter_grid, scoring="accuracy", cv=2, n_jobs=-1, verbose=False
        )
        self.model.fit(ds.x_train, ds.y_train)

        layer.log({"xgboost best parameters": self.model.best_params_})
        preds = self.model.predict(ds.x_test)
        self.score = accuracy_score(ds.y_test, preds)
        self.feature_importances = self.model.best_estimator_.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score
