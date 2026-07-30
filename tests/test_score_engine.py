import pandas as pd

from app.ai.score_engine import ScoreEngine


def test_score_engine():

    df = pd.DataFrame(
        {
            "trend_market": [True],
            "macd_bullish": [True],
            "volume_spike": [True],
            "hammer": [True],
        }
    )

    score, reasons = ScoreEngine.score(df)

    assert score > 0

    assert len(reasons) > 0