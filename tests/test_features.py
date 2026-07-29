import pandas as pd

from app.ai.features import FeatureExtractor


def test_feature_extractor():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_20": 99,
                "ema_50": 95,
                "rsi": 55,
                "atr": 2,
            }
        ]
    )

    features = FeatureExtractor.extract(df)

    assert features["close"] == 100
    assert features["ema20"] == 99
    assert features["ema50"] == 95
    assert features["rsi"] == 55
    assert features["atr"] == 2