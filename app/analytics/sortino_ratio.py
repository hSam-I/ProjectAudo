import math


class SortinoRatio:
    """
    Calculates annualized Sortino Ratio.
    """

    @staticmethod
    def calculate(
        returns: list[float],
        target_return: float = 0.0,
    ) -> float:

        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)

        downside_returns = [
            r - target_return
            for r in returns
            if r < target_return
        ]

        if not downside_returns:
            return 0.0

        downside_variance = sum(
            r**2
            for r in downside_returns
        ) / len(downside_returns)

        downside_deviation = math.sqrt(
            downside_variance
        )

        if downside_deviation == 0:
            return 0.0

        sortino = (
            (mean_return - target_return)
            / downside_deviation
        ) * math.sqrt(252)

        return round(sortino, 2)