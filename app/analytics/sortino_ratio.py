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
            # No period fell below the target: the denominator (downside
            # deviation) is 0. Since downside_returns is only empty when
            # every return is >= target_return, mean_return - target_return
            # is never negative here - collapsing this to 0.0 would make an
            # all-win window read identically to a genuinely flat/no-edge
            # one, which is exactly what misled walk-forward interpretation.
            excess = mean_return - target_return

            if excess > 0:
                return float("inf")

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