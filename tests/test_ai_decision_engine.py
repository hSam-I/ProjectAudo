import pandas as pd

from app.core.enums import Signal
from app.decision.ai_decision_engine import AIDecisionEngine
from app.strategy.base_strategy import BaseStrategy


class DummyStrategy(BaseStrategy):

    def generate_signal(self, df):
        return Signal.BUY


def test_ai_decision_engine():

    df = pd.DataFrame(
        [
            {
                "close": 100,
                "ema_20": 105,
                "ema_50": 100,
                "rsi": 60,
                "atr": 2,
                "macd_histogram": 1,
            }
        ]
    )

    engine = AIDecisionEngine(
        strategy=DummyStrategy()
    )

    decision = engine.evaluate(
        df=df,
        base_risk=0.02,
    )

    assert decision is not None