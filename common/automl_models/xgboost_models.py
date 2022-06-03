from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV

from ..automl import AutoMLModel, TrainDataset
from xgboost import XGBClassifier


class XGBoostClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("XGBoost Classifier", AutoMLModel.CLASSIFIER)

    def train(
        self,
        ds: TrainDataset
    ) -> None:
        hyperparameter_grid = {
            'n_estimators': [100, 500, 900, 1100, 1500],
            'max_depth': [2, 3, 5, 10, 15],
            'learning_rate': [0.05, 0.1, 0.15, 0.20],
            'min_child_weight': [1, 2, 3, 4]
        }

        estimator = XGBClassifier(seed=42)
        self.model = GridSearchCV(
            estimator=estimator,
            param_grid=hyperparameter_grid,
            scoring='accuracy',
            n_jobs=10,
            cv=10,
            verbose=True
        )

        self.model.fit(ds.x_train, ds.y_train)
        preds = self.model.predict(ds.x_test)
        self.score = accuracy_score(ds.y_test, preds)

    def compare_score(self, score: float) -> bool:
        return self.score > score
