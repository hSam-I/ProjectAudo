from app.portfolio.portfolio_manager import PortfolioManager


class RiskLimits:
    """
    Portfolio risk limit controller.
    """

    def __init__(
        self,
        portfolio: PortfolioManager,
        max_total_risk: float,
        max_positions: int,
    ):

        self.portfolio = portfolio
        self.max_total_risk = max_total_risk
        self.max_positions = max_positions

    def can_open_position(
        self,
        risk_amount: float,
    ) -> bool:

        if self.portfolio.count() >= self.max_positions:
            return False

        current_risk = sum(
            trade.risk_amount
            for trade in self.portfolio.open_positions()
        )

        return (
            current_risk + risk_amount
            <= self.max_total_risk
        )