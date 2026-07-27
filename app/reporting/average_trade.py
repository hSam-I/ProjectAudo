from app.backtesting.portfolio import Portfolio


class AverageTrade:
    """
    Average trade statistics.
    """

    @staticmethod
    def average_win(
        portfolio: Portfolio,
    ) -> float:

        winners = [
            trade.profit
            for trade in portfolio.closed_trades
            if trade.profit > 0
        ]

        if not winners:
            return 0.0

        return sum(winners) / len(winners)

    @staticmethod
    def average_loss(
        portfolio: Portfolio,
    ) -> float:

        losers = [
            abs(trade.profit)
            for trade in portfolio.closed_trades
            if trade.profit < 0
        ]

        if not losers:
            return 0.0

        return sum(losers) / len(losers)

    @staticmethod
    def average_trade(
        portfolio: Portfolio,
    ) -> float:

        trades = portfolio.closed_trades

        if not trades:
            return 0.0

        return (
            sum(
                trade.profit
                for trade in trades
            )
            / len(trades)
        )