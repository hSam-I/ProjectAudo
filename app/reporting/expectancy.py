from app.backtesting.portfolio import Portfolio


class Expectancy:
    """
    Calculates trading expectancy.
    """

    @staticmethod
    def calculate(
        portfolio: Portfolio,
    ) -> float:

        trades = portfolio.closed_trades

        if not trades:
            return 0.0

        winners = [
            trade.profit
            for trade in trades
            if trade.profit > 0
        ]

        losers = [
            abs(trade.profit)
            for trade in trades
            if trade.profit < 0
        ]

        total = len(trades)

        win_rate = len(winners) / total
        loss_rate = len(losers) / total

        average_win = (
            sum(winners) / len(winners)
            if winners
            else 0.0
        )

        average_loss = (
            sum(losers) / len(losers)
            if losers
            else 0.0
        )

        return (
            win_rate * average_win
            - loss_rate * average_loss
        )