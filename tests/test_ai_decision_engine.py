import pandas as pd

from app.decision.ai_decision_engine import AIDecisionEngine


def test_ai_decision_engine():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_fast": 105,
                "ema_slow": 100,
                "rsi": 60,
                "atr": 2,
                "macd": 1.5,
                "macd_signal": 1.2,
                "macd_histogram": 0.3,
            }
        ]
    )

    engine = AIDecisionEngine()

    decision = engine.evaluate(
        df=df,
        base_risk=0.02,
    )

    assert decision is not None
    assert decision.signal is not None
    assert decision.risk > 0