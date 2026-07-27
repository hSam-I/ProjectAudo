import pandas as pd

from app.decision.decision_engine import DecisionEngine
from app.strategy.base_strategy import BaseStrategy


class DummyStrategy(BaseStrategy):

    def generate_signal(
        self,
        df: pd.DataFrame,
    ) -> str:

        return "BUY"


def test_decision_engine_accepts_strategy():

    engine = DecisionEngine(
        strategy=DummyStrategy(),
    )

    assert isinstance(
        engine.strategy,
        BaseStrategy,
    )