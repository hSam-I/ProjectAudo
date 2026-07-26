from app.strategy.base_strategy import BaseStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy


def test_strategy_interface():

    strategy = EMARSIStrategy()

    assert isinstance(
        strategy,
        BaseStrategy,
    )