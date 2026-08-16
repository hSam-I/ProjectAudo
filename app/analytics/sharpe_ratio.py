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
            # Zero variance: the ratio's denominator is 0, so it is only
            # truly undefined (0.0) when there is also no excess return.
            # A nonzero constant excess return with zero risk is a real,
            # unbounded reward-to-risk outcome, not "no edge" - collapsing
            # it to 0.0 would be indistinguishable from a genuinely flat
            # or bad result.
            if mean > 0:
                return float("inf")
            if mean < 0:
                return float("-inf")
            return 0.0

        sharpe = (mean / std) * math.sqrt(252)

        return round(sharpe, 2)