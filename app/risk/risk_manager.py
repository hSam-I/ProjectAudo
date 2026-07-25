from app.config.settings import settings


class RiskManager:
    """
    Calculates risk values used by both the
    backtester and the live trading engine.
    """

    def __init__(self):

        self.risk_percent = settings.risk_percent / 100

    def risk_amount(self, balance: float) -> float:
        """Maximum dollar amount to risk."""

        return balance * self.risk_percent

    def stop_loss_distance(self, atr: float) -> float:
        """Distance between entry and stop-loss."""

        return atr * 2

    def stop_loss(self, entry_price: float, atr: float) -> float:
        """Stop-loss price."""

        return entry_price - self.stop_loss_distance(atr)

    def take_profit(self, entry_price: float, atr: float) -> float:
        """Take-profit price."""

        return entry_price + (self.stop_loss_distance(atr) * 2)