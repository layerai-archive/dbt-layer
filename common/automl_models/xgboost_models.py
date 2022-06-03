import layer
import pandas as pd  # type: ignore
from sklearn.metrics import accuracy_score  # type: ignore
from sklearn.model_selection import GridSearchCV  # type: ignore
from xgboost import XGBClassifier

from .base_model import AutoMLModel, TrainDataset


class XGBoostClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("XGBoost Classifier", AutoMLModel.CLASSIFIER)

    def train(self, ds: TrainDataset) -> None:
        hyperparameter_grid = {
            "max_depth": range(2, 10, 1),
            "n_estimators": range(60, 220, 40),
            "learning_rate": [0.1, 0.01, 0.05],
        }

        df = pd.DataFrame({"name": hyperparameter_grid.keys(), "value": hyperparameter_grid.values()})
        df = df.set_index("name")
        layer.log({"xgboost hyperparameter grid": df})

        estimator = XGBClassifier(seed=42, eval_metric="mlogloss", use_label_encoder=False)
        self.model: GridSearchCV = GridSearchCV(
            estimator=estimator, param_grid=hyperparameter_grid, scoring="accuracy", cv=3, n_jobs=-1, verbose=False
        )
        self.model.fit(ds.x_train, ds.y_train)

        df = pd.DataFrame({"name": self.model.best_params_.keys(), "value": self.model.best_params_.values()})
        df = df.set_index("name")
        layer.log({"xgboost best parameters": df})
        preds = self.model.predict(ds.x_test)
        self.score = accuracy_score(ds.y_test, preds)
        self.feature_importances = self.model.best_estimator_.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score
