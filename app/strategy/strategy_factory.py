from app.strategy.base_strategy import BaseStrategy
from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.mean_reversion_strategy import MeanReversionStrategy
from app.strategy.scalping_strategy import ScalpingStrategy
from app.strategy.swing_strategy import SwingStrategy
from app.strategy.trend_following_strategy import TrendFollowingStrategy


class StrategyFactory:
    """
    Factory responsible for creating
    strategy instances.
    """

    _strategies = {
        "trend_following": TrendFollowingStrategy,
        "mean_reversion": MeanReversionStrategy,
        "breakout": BreakoutStrategy,
        "scalping": ScalpingStrategy,
        "swing": SwingStrategy,
    }

    @classmethod
    def create(
        cls,
        name: str,
    ) -> BaseStrategy:

        strategy = cls._strategies.get(name)

        if strategy is None:
            raise ValueError(
                f"Unknown strategy: {name}"
            )

        return strategy()

    @classmethod
    def available_strategies(cls):

        return sorted(cls._strategies.keys())

    @classmethod
    def register(
        cls,
        name: str,
        strategy: type[BaseStrategy],
    ):

        cls._strategies[name] = strategy