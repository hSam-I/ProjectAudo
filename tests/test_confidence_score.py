import pandas as pd

from app.ai.confidence import ConfidenceScore


def test_confidence():

    df = pd.DataFrame(
    [
        {
            "close": 100,
            "ema_20": 105,
            "ema_50": 100,
            "rsi": 60,
            "atr": 2,
        }
    ]
)

    confidence = ConfidenceScore.calculate(df)

    assert confidence == 1.0