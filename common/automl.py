from typing import Any, List, Type

import pandas as pd  # type: ignore

import layer
from common.automl_models.base_model import AutoMLModel, TrainDataset
from common.automl_models.sklearn_models import (
    ScikitLearnAdaBoostClassifier,
    ScikitLearnDecisionTreeClassifier,
    ScikitLearnDecisionTreeRegressor,
    ScikitLearnLinearRegression,
    ScikitLearnRandomForestClassifier,
    ScikitLearnRidgeClassifier,
)
from common.automl_models.xgboost_models import XGBoostClassifier, XGBoostRegressor
from layer.decorators import model as model_decorator


class AutoML:
    automl_models: List[Type[AutoMLModel]] = [
        # sklearn models
        ScikitLearnRandomForestClassifier,
        ScikitLearnDecisionTreeClassifier,
        ScikitLearnAdaBoostClassifier,
        ScikitLearnRidgeClassifier,
        ScikitLearnLinearRegression,
        ScikitLearnDecisionTreeRegressor,
        # xgboost models
        XGBoostClassifier,
        XGBoostRegressor,
    ]

    def __init__(self, model_type: str, df: pd.DataFrame, features: List[str], target: str) -> None:
        self.model_type = model_type
        self.df = df
        self.features = features
        self.target = target
        self.score = None

    def train(self, project_name: str, model_name: str) -> None:
        if self.model_type not in [AutoMLModel.CLASSIFIER, AutoMLModel.REGRESSOR]:
            raise Exception(f"Model type '{self.model_type}' not supported yet!")

        def log_models(trained_models: List[AutoMLModel]) -> None:
            model_comparison = {model.name: model.score for model in trained_models}
            layer.log({"models": model_comparison})

        def training_func() -> Any:
            # Prepare dataset
            train_dataset = TrainDataset(self.df, self.features, self.target)

            # Run all models matches the requested model type
            best_model = None
            best_score = 0

            trained_models = []
            for automl_model in self.automl_models:
                trainer = automl_model()

                if trainer.model_type == self.model_type:
                    trained_models.append(trainer)
                    trainer.train(train_dataset)
                    if trainer.compare_score(best_score):
                        best_model = trainer
                        best_score = trainer.score

                    # Update models scoreboard after training
                    log_models(trained_models)

            if best_model is None:
                raise Exception("AutoML failed! Check your model type!")

            trained_model = best_model.model

            layer.log({"best model": best_model.name})
            layer.log({"best score": best_score})

            if best_model.feature_importances is not None:
                import matplotlib as plt  # type: ignore

                plt.use("agg")
                feat_importances = pd.DataFrame(
                    best_model.feature_importances, index=self.features, columns=["Importance"]
                )
                feat_importances.sort_values(by="Importance", ascending=False, inplace=True)
                layer.log({"feature importances": feat_importances.plot(kind="bar", figsize=(12, 7))})

            return trained_model

        model_decorator(model_name)(training_func)()  # pylint: disable=no-value-for-parameter
