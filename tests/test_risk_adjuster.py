import pandas as pd

from app.ai.risk_adjuster import RiskAdjuster


def test_risk_adjuster():

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

    risk = RiskAdjuster.adjusted_risk(
        df=df,
        base_risk=0.02,
    )

    assert risk > 0