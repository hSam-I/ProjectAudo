import pandas as pd

from app.ai.scoring import MarketScore


def test_market_score():

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

    score = MarketScore.calculate(df)

    assert score == 3