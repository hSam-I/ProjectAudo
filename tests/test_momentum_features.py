import pandas as pd

from app.features.momentum_features import (
    MomentumFeatures,
)


def test_momentum_features():

    df = pd.DataFrame(
        {
            "rsi": [25, 75],
            "macd": [-1, 2],
            "macd_signal": [-2, 1],
            "macd_histogram": [-0.2, 0.5],
        }
    )

    df = MomentumFeatures.build(df)

    assert "rsi_overbought" in df.columns
    assert "rsi_oversold" in df.columns

    assert "macd_positive" in df.columns
    assert "macd_bullish" in df.columns
    assert "macd_hist_positive" in df.columns