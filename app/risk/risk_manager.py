class RiskManager:

    def __init__(self, risk_percent: float = 0.01):
        self.risk_percent = risk_percent

    def risk_amount(self, balance: float) -> float:
        return balance * self.risk_percent

    def stop_loss(self, price: float, atr: float) -> float:
        return price - (atr * 2)

    def take_profit(self, price: float, atr: float) -> float:
        return price + (atr * 4)