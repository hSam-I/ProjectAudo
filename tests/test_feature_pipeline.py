import pandas as pd

from app.features.feature_pipeline import (
    FeaturePipeline,
)


def test_feature_pipeline():

    df = pd.DataFrame(
        {
            "open": list(range(1, 150)),
            "high": list(range(2, 151)),
            "low": list(range(0, 149)),
            "close": list(range(1, 150)),
            "volume": [100] * 149,
        }
    )

    df = FeaturePipeline.build(df)

    assert "ema_fast" in df.columns
    assert "ema_slow" in df.columns
    assert "rsi" in df.columns
    assert "atr" in df.columns
    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_histogram" in df.columns