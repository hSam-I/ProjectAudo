import pandas as pd

from app.features.pattern_features import (
    PatternFeatures,
)


def test_pattern_features():

    df = pd.DataFrame(
        {
            "open": [100, 102],
            "high": [105, 103],
            "low": [95, 99],
            "close": [104, 100],
        }
    )

    df = PatternFeatures.build(df)

    assert "body" in df.columns
    assert "range" in df.columns

    assert "upper_shadow" in df.columns
    assert "lower_shadow" in df.columns

    assert "body_ratio" in df.columns

    assert "doji" in df.columns

    assert "bull_candle" in df.columns
    assert "bear_candle" in df.columns

    assert "hammer" in df.columns
    assert "shooting_star" in df.columns