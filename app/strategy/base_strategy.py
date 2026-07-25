from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        pass