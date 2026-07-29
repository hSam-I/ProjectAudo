from app.portfolio.portfolio_manager import PortfolioManager


class PerformanceTracker:
    """
    Tracks portfolio performance.
    """

    def __init__(self, portfolio: PortfolioManager):

        self.portfolio = portfolio

    def exposure(self) -> float:

        return self.portfolio.total_exposure()

    def positions(self) -> int:

        return self.portfolio.count()

    def has_open_positions(self) -> bool:

        return self.positions() > 0