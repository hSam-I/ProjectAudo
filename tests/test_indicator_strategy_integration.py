import pandas as pd

from app.indicators.indicator_engine import IndicatorEngine
from app.strategy.trend_following_strategy import (
    TrendFollowingStrategy,
)


def test_indicator_strategy_integration():

    df = pd.DataFrame(
        {
            "open": list(range(1, 200)),
            "high": list(range(2, 201)),
            "low": list(range(0, 199)),
            "close": list(range(1, 200)),
            "volume": [1000] * 199,
        }
    )

    df = IndicatorEngine.prepare(
        df=df,
        ema_fast=10,
        ema_slow=30,
    )

    strategy = TrendFollowingStrategy(
        ema_fast=10,
        ema_slow=30,
    )

    signal = strategy.generate_signal(df)

    assert signal is not None