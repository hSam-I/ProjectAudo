import pandas as pd

from app.ai.features import FeatureExtractor


def test_feature_extractor():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_fast": 99,
                "ema_slow": 95,
                "rsi": 55,
                "atr": 2,
                "macd": 1.2,
                "macd_signal": 1.0,
                "macd_histogram": 0.2,
            }
        ]
    )

    features = FeatureExtractor.extract(df)

    assert features["close"] == 100
    assert features["ema_fast"] == 99
    assert features["ema_slow"] == 95
    assert features["rsi"] == 55
    assert features["atr"] == 2
    assert features["macd"] == 1.2
    assert features["macd_signal"] == 1.0
    assert features["macd_histogram"] == 0.2