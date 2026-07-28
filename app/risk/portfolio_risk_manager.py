from app.config.settings import settings


class PortfolioRiskManager:
    """
    Controls portfolio level risk.
    """

    @staticmethod
    def can_open_position(portfolio) -> bool:

        return (
            portfolio.open_trades
            < settings.max_open_positions
        )

    @staticmethod
    def portfolio_risk(portfolio) -> float:

        risk = 0.0

        for trade in portfolio.open_positions:
            risk += trade.risk_amount

        return risk

    @staticmethod
    def can_take_risk(
        portfolio,
        new_trade_risk: float,
    ) -> bool:

        current = PortfolioRiskManager.portfolio_risk(
            portfolio
        )

        maximum = (
            portfolio.balance
            * settings.max_portfolio_risk
        )

        return (
            current + new_trade_risk
            <= maximum
        )