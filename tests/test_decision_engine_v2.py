import pandas as pd

from app.decision.decision_engine import DecisionEngine


def test_decision_engine():

    df = pd.DataFrame(
        {
            "trend_market": [True],
            "bear_market": [False],
            "sideways_market": [False],
            "high_volatility_market": [False],
            "low_volatility_market": [False],
            "breakout": [False],

            "macd_bullish": [True],
            "volume_spike": [True],
            "hammer": [True],

            "ema_fast": [102],
            "ema_slow": [100],
            "adx": [30],
            "rsi": [60],
            "macd": [1],
            "macd_signal": [0.5],
        }
    )

    decision = DecisionEngine().evaluate(df)

    assert decision.score > 0