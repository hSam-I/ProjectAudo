from app.backtesting.trade import Trade


class ProfitFactor:
    """
    Calculates Profit Factor.
    """

    @staticmethod
    def calculate(
        trades: list[Trade],
    ) -> float:

        gross_profit = sum(
            trade.profit
            for trade in trades
            if trade.profit > 0
        )

        gross_loss = abs(
            sum(
                trade.profit
                for trade in trades
                if trade.profit < 0
            )
        )

        if gross_loss == 0:
            return 0.0

        return round(
            gross_profit / gross_loss,
            2,
        )