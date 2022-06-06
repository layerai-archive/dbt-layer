from abc import abstractmethod
from typing import Any, List

import pandas as pd  # type: ignore
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier  # type: ignore
from sklearn.linear_model import LinearRegression, RidgeClassifier  # type: ignore
from sklearn.metrics import r2_score, roc_auc_score  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor  # type: ignore

import layer
from layer.decorators import model as model_decorator


class AutoMLModel:
    # model types
    CLASSIFIER = "classifier"
    REGRESSOR = "regressor"

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


class ScikitLearnLinearRegression(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn LinearRegression", AutoMLModel.REGRESSOR)

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
        model = LinearRegression(normalize=True, fit_intercept=False, copy_X=True)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        model_accuracy = r2_score(y_test, y_pred)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnDecisionTreeRegressor(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn DecisionTreeRegressor", AutoMLModel.REGRESSOR)

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
        model = DecisionTreeRegressor(max_depth=7)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        model_accuracy = r2_score(y_test, y_pred)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnRandomForestClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn RandomForestClassifier", AutoMLModel.CLASSIFIER)

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


class ScikitLearnRidgeClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn RidgeClassifier", AutoMLModel.CLASSIFIER)

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
        model = RidgeClassifier()
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        model_accuracy = roc_auc_score(y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnDecisionTreeClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn DecisionTreeClassifier", AutoMLModel.CLASSIFIER)

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
        model = DecisionTreeClassifier(max_depth=5)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        model_accuracy = roc_auc_score(y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnAdaBoostClassifier(AutoMLModel):
    def __init__(self) -> None:
        super().__init__("Scikit-Learn AdaBoostClassifier", AutoMLModel.CLASSIFIER)

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
        model = AdaBoostClassifier()
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        model_accuracy = roc_auc_score(y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class AutoML:
    automl_models = [
        ScikitLearnRandomForestClassifier(),
        ScikitLearnDecisionTreeClassifier(),
        ScikitLearnAdaBoostClassifier(),
        ScikitLearnRidgeClassifier(),
        ScikitLearnLinearRegression(),
        ScikitLearnDecisionTreeRegressor(),
    ]

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
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.30, random_state=42)
        x_test, x_val, y_test, y_val = train_test_split(x_test, y_test, test_size=0.5, random_state=42)

        # Run all models matches the requested model type
        best_model = None
        best_score = 0
        for automl_model in self.automl_models:
            if automl_model.model_type == self.model_type:
                print(f"Training with {automl_model.name}")
                automl_model.train(x_train, y_train, x_test, y_test, x_val, y_val, self.features, self.target)
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
