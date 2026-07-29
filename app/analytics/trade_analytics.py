from app.backtesting.trade import Trade


class TradeAnalytics:
    """
    Calculates trade statistics.
    """

    @staticmethod
    def total_profit(trades: list[Trade]) -> float:

        return sum(trade.profit for trade in trades)

    @staticmethod
    def winners(trades: list[Trade]) -> int:

        return sum(
            1
            for trade in trades
            if trade.profit > 0
        )

    @staticmethod
    def losers(trades: list[Trade]) -> int:

        return sum(
            1
            for trade in trades
            if trade.profit <= 0
        )

    @staticmethod
    def win_rate(trades: list[Trade]) -> float:

        if not trades:
            return 0.0

        return (
            TradeAnalytics.winners(trades)
            / len(trades)
        ) * 100