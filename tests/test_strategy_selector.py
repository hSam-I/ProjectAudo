import pandas as pd

from app.ai.strategy_selector import StrategySelector
from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy


def test_strategy_selector():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_20": 105,
                "ema_50": 100,
                "atr": 2,
            }
        ]
    )

    strategy = StrategySelector.select(df)

    assert isinstance(
        strategy,
        (EMARSIStrategy, BreakoutStrategy),
    )