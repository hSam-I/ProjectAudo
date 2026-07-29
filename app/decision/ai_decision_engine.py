from app.ai.risk_adjuster import RiskAdjuster
from app.ai.trade_filter import TradeFilter
from app.decision.decision_engine import DecisionEngine


class AIDecisionEngine:
    """
    AI enhanced decision engine.
    """

    def __init__(self, strategy=None):

        self.engine = DecisionEngine(
            strategy=strategy,
        )

    def evaluate(
        self,
        df,
        base_risk: float,
    ):

        if not TradeFilter.should_trade(df):
            return None

        decision = self.engine.evaluate(df)

        decision.risk = RiskAdjuster.adjusted_risk(
            df=df,
            base_risk=base_risk,
        )

        return decision