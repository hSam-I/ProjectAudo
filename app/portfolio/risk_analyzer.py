from app.portfolio.portfolio_manager import PortfolioManager


class RiskAnalyzer:
    """
    Portfolio level risk calculations.
    """

    def __init__(self, portfolio: PortfolioManager):

        self.portfolio = portfolio

    def total_risk(self) -> float:

        return sum(
            trade.risk_amount
            for trade in self.portfolio.open_positions()
        )

    def average_risk(self) -> float:

        positions = self.portfolio.count()

        if positions == 0:
            return 0.0

        return self.total_risk() / positions

    def max_risk(self) -> float:

        positions = self.portfolio.open_positions()

        if not positions:
            return 0.0

        return max(
            trade.risk_amount
            for trade in positions
        )