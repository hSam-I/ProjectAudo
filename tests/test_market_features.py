import pandas as pd

from app.features.market_features import (
    MarketFeatures,
)


def test_market_features():

    df = pd.DataFrame(
        {
            "close": [100],
            "adx": [30],
            "ema_fast": [105],
            "ema_slow": [95],
            "atr_percent": [2.5],
            "bb_upper": [99],
            "bb_lower": [90],
            "senkou_span_a": [95],
            "senkou_span_b": [94],
        }
    )

    df = MarketFeatures.build(df)

    assert "trend_market" in df.columns
    assert "bear_market" in df.columns
    assert "sideways_market" in df.columns

    assert "high_volatility_market" in df.columns
    assert "low_volatility_market" in df.columns

    assert "breakout" in df.columns
    assert "breakdown" in df.columns

    assert "above_cloud" in df.columns
    assert "below_cloud" in df.columns