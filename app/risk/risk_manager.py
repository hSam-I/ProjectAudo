class RiskManager:

    def __init__(
        self,
        risk_per_trade: float = 0.01,
    ):
        self.risk_per_trade = risk_per_trade

    def calculate_risk(self, balance: float):

        return balance * self.risk_per_trade