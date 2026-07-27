from app.backtesting.portfolio import Portfolio


class ProfitFactor:
    """
    Calculates the Profit Factor.

    Profit Factor =
        Gross Profit / Gross Loss
    """

    @staticmethod
    def calculate(
        portfolio: Portfolio,
    ) -> float:

        gross_profit = sum(
            trade.profit
            for trade in portfolio.closed_trades
            if trade.profit > 0
        )

        gross_loss = abs(
            sum(
                trade.profit
                for trade in portfolio.closed_trades
                if trade.profit < 0
            )
        )

        if gross_loss == 0:

            if gross_profit == 0:
                return 0.0

            return float("inf")

        return gross_profit / gross_loss