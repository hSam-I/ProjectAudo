from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """
    Base interface for all trading strategies.
    """

    @abstractmethod
    def generate_signal(
        self,
        df: pd.DataFrame,
    ) -> str:
        """
        Returns BUY, SELL or HOLD.
        """
        raise NotImplementedError