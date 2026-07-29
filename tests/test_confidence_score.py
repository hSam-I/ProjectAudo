import pandas as pd

from app.ai.confidence import ConfidenceScore


def test_confidence():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_20": 105,
                "ema_50": 100,
                "rsi": 55,
                "atr": 2,
                "macd": 1.2,
                "macd_signal": 1.0,
                "macd_histogram": 0.2,
            }
        ]
    )

    confidence = ConfidenceScore.calculate(df)

    assert 0 <= confidence <= 2