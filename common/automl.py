from abc import abstractmethod
from typing import Any, List

import layer
import pandas as pd  # type: ignore
from layer.decorators import model as model_decorator
from sklearn.ensemble import RandomForestClassifier  # type: ignore
from sklearn.metrics import roc_auc_score  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from xgboost import XGBClassifier


class AutoMLModel:
    score = 0
    model = None
    name = None

    def __init__(self, name: str, model_type: str) -> None:
        self.model_type = model_type
        self.name = name

    @abstractmethod
    def train(
        self,
        x_train: pd.DataFrame,
        y_train: pd.DataFrame,
        x_test: pd.DataFrame,
        y_test: pd.DataFrame,
        x_val: pd.DataFrame,
        y_val: pd.DataFrame,
        features: List[str],
        target: str,
    ) -> Any:
        """

        :return:
        """

    def compare_score(self, score: float) -> bool:
        """

        :return:
        """


class AutoSKLearnClassifierModel(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("SKLearn", "classifier")

    def train(
        self,
        x_train: pd.DataFrame,
        y_train: pd.DataFrame,
        x_test: pd.DataFrame,
        y_test: pd.DataFrame,
        x_val: pd.DataFrame,
        y_val: pd.DataFrame,
        features: List[str],
        target: str,
    ) -> None:
        model = RandomForestClassifier()
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        model_accuracy = roc_auc_score(y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class AutoXGBoostClassifierModel(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("XGBoost", "classifier")

    def train(
        self,
        x_train: pd.DataFrame,
        y_train: pd.DataFrame,
        x_test: pd.DataFrame,
        y_test: pd.DataFrame,
        x_val: pd.DataFrame,
        y_val: pd.DataFrame,
        features: List[str],
        target: str,
    ) -> None:
        model = XGBClassifier(max_depth=5, verbosity=0, learning_rate=0.1, subsample=0.5, n_estimators=100, n_jobs=-1)
        model.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_val, y_val)], verbose=False)
        predictions = model.predict(x_test)
        self.score = roc_auc_score(y_test, predictions)
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class AutoML:
    automl_models = [AutoSKLearnClassifierModel(), AutoXGBoostClassifierModel()]

    def __init__(self, model_type: str, df: pd.DataFrame, features: List[str], target: str) -> None:
        self.model_type = model_type
        self.df = df
        self.features = features
        self.target = target
        self.score = None

    def train(self, project_name: str, model_name: str) -> None:
        x = self.df.drop([self.target], axis=1)
        y = self.df[self.target]

        # Prepare train, test and validation datasets
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30)
        x_test, x_val, y_test, y_val = train_test_split(x_test, y_test, test_size=0.5)

        # Run all models matches the requested model type
        best_model = None
        best_score = 0
        for automl_model in self.automl_models:
            if automl_model.model_type == self.model_type:
                automl_model.train(x_train, y_train, x_test, y_test, x_val, y_val, self.features, self.target)
                print(f"Training with {automl_model.name}")
                print(f"  Completed with score: {automl_model.score:.4f}")
                if automl_model.compare_score(best_score):
                    best_model = automl_model
                    best_score = automl_model.score
        if best_model is None:
            raise Exception(f"Model type '{self.model_type}' not supported yet!")
        else:
            print(f"Best ML model is {best_model.name} with score {best_score:.4f} ")
            layer.login()
            layer.init(project_name)
            trained_model = best_model.model

            def training_func() -> Any:
                layer.log({"score": best_score})
                return trained_model

            model_decorator(model_name)(training_func)()  # pylint: disable=no-value-for-parameter
