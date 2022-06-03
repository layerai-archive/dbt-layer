from abc import abstractmethod
from typing import Any, List

import layer
import pandas as pd  # type: ignore
from layer.decorators import model as model_decorator
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier  # type: ignore
from sklearn.linear_model import LinearRegression, RidgeClassifier  # type: ignore
from sklearn.metrics import r2_score, roc_auc_score  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor  # type: ignore

from common.automl_models.sklearn_models import (
    ScikitLearnAdaBoostClassifier,
    ScikitLearnDecisionTreeClassifier,
    ScikitLearnRandomForestClassifier,
    ScikitLearnRidgeClassifier,
    ScikitLearnDecisionTreeRegressor,
    ScikitLearnLinearRegression,
)
from common.automl_models.xgboost_models import XGBoostClassifier


class TrainDataset:
    def __init__(self, features: List[str], target):
        x = self.df.drop([self.target], axis=1)
        y = self.df[self.target]

        # Prepare train, test and validation datasets
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=0.30, random_state=42)
        self.x_test, self.x_val, self.y_test, self.y_val = train_test_split(self.x_test, self.y_test, test_size=0.5,
                                                                            random_state=42)


class AutoMLModel:
    # model types
    CLASSIFIER = "classifier"
    REGRESSOR = "regressor"

    def __init__(self, name: str, model_type: str) -> None:
        self.model_type = model_type
        self.name = name
        self.model = None
        self.score = 0

    @abstractmethod
    def train(
        self,
        dataset: TrainDataset
    ) -> Any:
        """

        :return:
        """

    def compare_score(self, score: float) -> bool:
        """

        :return:
        """


class AutoML:
    automl_models = [
        # sklearn models
        ScikitLearnRandomForestClassifier(),
        ScikitLearnDecisionTreeClassifier(),
        ScikitLearnAdaBoostClassifier(),
        ScikitLearnRidgeClassifier(),
        ScikitLearnLinearRegression(),
        ScikitLearnDecisionTreeRegressor(),
        # xgboost models
        XGBoostClassifier()
    ]

    def __init__(self, model_type: str, df: pd.DataFrame, features: List[str], target: str) -> None:
        self.model_type = model_type
        self.df = df
        self.features = features
        self.target = target
        self.score = None

    def train(self, project_name: str, model_name: str) -> None:
        train_dataset = TrainDataset(self.features, self.target)

        # Run all models matches the requested model type
        best_model = None
        best_score = 0
        for automl_model in self.automl_models:
            if automl_model.model_type == self.model_type:
                print(f"Training with {automl_model.name}")
                automl_model.train(train_dataset)
                print(f"  Completed with score: {automl_model.score:.4f}")
                if best_model is None or automl_model.compare_score(best_score):
                    best_model = automl_model
                    best_score = automl_model.score
        if best_model is None:
            raise Exception(f"Model type '{self.model_type}' not supported yet!")
        else:
            print(f"Best ML model is {best_model.name} with score {best_score:.4f} ")
            layer.login()
            # TODO Pass org name with project name
            layer.init(project_name)
            trained_model = best_model.model

            def training_func() -> Any:

                layer.log({"score": best_score})
                return trained_model

            # Register this model to Layer
            model_decorator(model_name)(training_func)()  # pylint: disable=no-value-for-parameter
