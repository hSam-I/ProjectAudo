import pandas as pd

from app.indicators.indicator_engine import IndicatorEngine
from app.strategy.trend_following_strategy import (
    TrendFollowingStrategy,
)


def test_indicator_strategy_integration():

    df = pd.DataFrame(
        {
            "close": list(range(1, 200)),
            "rsi": [60] * 199,
        }
    )

    df = IndicatorEngine.prepare(
        df,
        ema_fast=10,
        ema_slow=30,
    )

    strategy = TrendFollowingStrategy()

    signal = strategy.generate_signal(
        df,
    )

    assert signal is not None