from app.portfolio.portfolio_manager import PortfolioManager


class PortfolioStatistics:
    """
    Portfolio statistics.
    """

    def __init__(self, portfolio: PortfolioManager):

        self.portfolio = portfolio

    def exposure(self) -> float:

        return self.portfolio.total_exposure()

    def positions(self) -> int:

        return self.portfolio.count()

    def average_position_size(self) -> float:

        if self.positions() == 0:
            return 0.0

        return self.exposure() / self.positions()