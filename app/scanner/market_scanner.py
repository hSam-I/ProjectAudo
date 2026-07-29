from app.decision.decision_engine import DecisionEngine


class MarketScanner:
    """
    Scans multiple markets and returns decisions.
    """

    def __init__(
        self,
        strategy=None,
    ):

        self.decision_engine = DecisionEngine(
            strategy=strategy,
        )

    def scan(
        self,
        market_data: dict,
    ) -> dict:

        decisions = {}

        for symbol, df in market_data.items():

            decision = self.decision_engine.evaluate(
                df
            )

            decisions[symbol] = decision

        return decisions