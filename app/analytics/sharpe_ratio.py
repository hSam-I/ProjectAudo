import math


class SharpeRatio:
    """
    Calculates annualized Sharpe Ratio.
    """

    @staticmethod
    def calculate(
        returns: list[float],
        risk_free_rate: float = 0.0,
    ) -> float:

        if len(returns) < 2:
            return 0.0

        excess_returns = [
            r - risk_free_rate
            for r in returns
        ]

        mean = sum(excess_returns) / len(excess_returns)

        variance = sum(
            (r - mean) ** 2
            for r in excess_returns
        ) / (len(excess_returns) - 1)

        std = math.sqrt(variance)

        if std == 0:
            return 0.0

        sharpe = (mean / std) * math.sqrt(252)

        return round(sharpe, 2)