from abc import abstractmethod
from typing import List

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

    def __init__(self) -> None:
        self.model = None
        self.score = 0
        self.feature_importances = None
        self.explainer = None

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the AutoML model that will be shown to the user.
        :return: Name
        """

    @property
    @abstractmethod
    def model_type(self) -> str:
        """
        Defines the model type
        :return: Model type
        """

    @abstractmethod
    def train(self, dataset: TrainDataset) -> None:
        """
        Trains an AutoML model with the dataset provided

        :param dataset: Dataset to be used in training
        :return: None
        """

    def compare_score(self, score: float) -> bool:
        """
        Compares the model score to define the best model
        :param score: Score of another model to be compared
        :return: True/False is the score is better/worse
        """
