from app.backtesting.portfolio import Portfolio


class Performance:
    """
    Portfolio performance metrics.
    """

    @staticmethod
    def total_trades(
        portfolio: Portfolio,
    ) -> int:

        return len(portfolio.closed_trades)

    @staticmethod
    def winning_trades(
        portfolio: Portfolio,
    ) -> int:

        return sum(
            trade.profit > 0
            for trade in portfolio.closed_trades
        )

    @staticmethod
    def losing_trades(
        portfolio: Portfolio,
    ) -> int:

        return sum(
            trade.profit <= 0
            for trade in portfolio.closed_trades
        )

    @staticmethod
    def win_rate(
        portfolio: Portfolio,
    ) -> float:

        total = Performance.total_trades(
            portfolio
        )

        if total == 0:
            return 0.0

        wins = Performance.winning_trades(
            portfolio
        )

        return wins / total