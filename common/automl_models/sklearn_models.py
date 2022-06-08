from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier  # type: ignore
from sklearn.linear_model import LinearRegression, RidgeClassifier  # type: ignore
from sklearn.metrics import accuracy_score, r2_score  # type: ignore
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor  # type: ignore

from .base_model import AutoMLModel, TrainDataset


class ScikitLearnLinearRegression(AutoMLModel):

    name = "Scikit-Learn LinearRegression"
    model_type = AutoMLModel.REGRESSOR

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = LinearRegression(normalize=True, fit_intercept=False, copy_X=True)
        model.fit(ds.x_train, ds.y_train)
        y_pred = model.predict(ds.x_test)
        model_accuracy = r2_score(ds.y_test, y_pred)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnDecisionTreeRegressor(AutoMLModel):

    name = "Scikit-Learn DecisionTreeRegressor"
    model_type = AutoMLModel.REGRESSOR

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = DecisionTreeRegressor(max_depth=7)
        model.fit(ds.x_train, ds.y_train)
        y_pred = model.predict(ds.x_test)
        model_accuracy = r2_score(ds.y_test, y_pred)

        self.score = model_accuracy
        self.model = model
        self.feature_importances = model.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnRandomForestClassifier(AutoMLModel):
    name = "Scikit-Learn RandomForestClassifier"
    model_type = AutoMLModel.CLASSIFIER

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = RandomForestClassifier()
        model.fit(ds.x_train, ds.y_train)
        predictions = model.predict(ds.x_test)
        model_accuracy = accuracy_score(ds.y_test, predictions)

        self.score = model_accuracy
        self.model = model
        self.feature_importances = model.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnRidgeClassifier(AutoMLModel):
    name = "Scikit-Learn RidgeClassifier"
    model_type = AutoMLModel.CLASSIFIER

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = RidgeClassifier()
        model.fit(ds.x_train, ds.y_train)
        predictions = model.predict(ds.x_test)
        model_accuracy = accuracy_score(ds.y_test, predictions)

        self.score = model_accuracy
        self.model = model

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnDecisionTreeClassifier(AutoMLModel):
    name = "Scikit-Learn DecisionTreeClassifier"
    model_type = AutoMLModel.CLASSIFIER

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = DecisionTreeClassifier(max_depth=5)
        model.fit(ds.x_train, ds.y_train)
        predictions = model.predict(ds.x_test)
        model_accuracy = accuracy_score(ds.y_test, predictions)

        self.score = model_accuracy
        self.model = model
        self.feature_importances = model.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score


class ScikitLearnAdaBoostClassifier(AutoMLModel):
    name = "Scikit-Learn AdaBoostClassifier"
    model_type = AutoMLModel.CLASSIFIER

    def __init__(self) -> None:
        super().__init__()

    def train(self, ds: TrainDataset) -> None:
        model = AdaBoostClassifier()
        model.fit(ds.x_train, ds.y_train)
        predictions = model.predict(ds.x_test)
        model_accuracy = accuracy_score(ds.y_test, predictions)

        self.score = model_accuracy
        self.model = model
        self.feature_importances = model.feature_importances_

    def compare_score(self, score: float) -> bool:
        return self.score > score
