import pandas as pd

from app.features.volatility_features import (
    VolatilityFeatures,
)


def test_volatility_features():

    df = pd.DataFrame(
        {
            "close": [100, 100],
            "atr": [3, 1],
            "bb_upper": [110, 103],
            "bb_middle": [100, 100],
            "bb_lower": [90, 97],
        }
    )

    df = VolatilityFeatures.build(df)

    assert "atr_percent" in df.columns
    assert "high_volatility" in df.columns

    assert "bb_width" in df.columns
    assert "bb_squeeze" in df.columns

    assert "bb_breakout_up" in df.columns
    assert "bb_breakout_down" in df.columns