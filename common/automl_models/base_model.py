from abc import abstractmethod
from typing import Any, List

import pandas as pd  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore


class TrainDataset:
    def __init__(self, df: pd.DataFrame, features: List[str], target: str):
        self.df = df
        self.features = features
        self.target = target
        x = self.df.drop([target], axis=1)
        y = self.df[target]

        # Prepare train, test and validation datasets
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=0.30, random_state=42)
        self.x_test, self.x_val, self.y_test, self.y_val = train_test_split(
            self.x_test, self.y_test, test_size=0.5, random_state=42
        )


class AutoMLModel:
    # model types
    CLASSIFIER = "classifier"
    REGRESSOR = "regressor"

    def __init__(self, name: str, model_type: str) -> None:
        self.model_type = model_type
        self.name = name
        self.model = None
        self.score = 0
        self.feature_importances = None
        self.explainer = None

    @abstractmethod
    def train(self, dataset: TrainDataset) -> Any:
        """

        :return:
        """

    def compare_score(self, score: float) -> bool:
        """

        :return:
        """
