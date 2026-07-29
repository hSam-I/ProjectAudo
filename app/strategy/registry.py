from app.strategy.base_strategy import BaseStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy
from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.trend_following_strategy import TrendFollowingStrategy
from app.strategy.mean_reversion_strategy import MeanReversionStrategy

_STRATEGIES = {
    "ema_rsi": EMARSIStrategy,
    "breakout": BreakoutStrategy,
    "trend_following": TrendFollowingStrategy,
    "mean_reversion": MeanReversionStrategy,
}

def get_strategy(name: str) -> BaseStrategy:
    """
    Returns a strategy instance by name.
    """

    try:
        strategy_class = _STRATEGIES[name.lower()]
    except KeyError as exc:
        raise ValueError(
            f"Unknown strategy: {name}"
        ) from exc

    return strategy_class()