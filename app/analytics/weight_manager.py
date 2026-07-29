from app.analytics.strategy_stats import StrategyStats


class WeightManager:
    """
    Calculates strategy voting weights
    based on historical performance.
    """

    @staticmethod
    def weight(stats: StrategyStats) -> float:

        if stats.trades == 0:
            return 1.0

        win_rate = stats.win_rate

        if win_rate >= 0.80:
            return 1.50

        if win_rate >= 0.60:
            return 1.25

        if win_rate >= 0.40:
            return 1.00

        return 0.75