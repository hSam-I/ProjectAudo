from abc import ABC, abstractmethod

from app.core.enums import Signal


class BaseStrategy(ABC):
    """
    Base interface for all trading strategies.
    """

    name = "base"

    description = "Base trading strategy."

    version = "1.0"

    @abstractmethod
    def generate_signal(self, df) -> Signal:
        """
        Returns BUY / SELL / HOLD.
        """
        raise NotImplementedError