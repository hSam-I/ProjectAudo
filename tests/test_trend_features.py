import pandas as pd

from app.features.trend_features import TrendFeatures


def test_trend_features():

    df = pd.DataFrame(
        {
            "close": [100, 101],
            "ema_fast": [101, 102],
            "ema_slow": [99, 100],
            "adx": [30, 35],
        }
    )

    df = TrendFeatures.build(df)

    assert "trend_up" in df.columns
    assert "trend_strength" in df.columns
    assert "strong_trend" in df.columns