class EquityCurve:
    """
    Portfolio equity curve calculations.
    """

    @staticmethod
    def cumulative(balance_history: list[float]) -> list[float]:

        return balance_history

    @staticmethod
    def highest(balance_history: list[float]) -> float:

        if not balance_history:
            return 0.0

        return max(balance_history)

    @staticmethod
    def lowest(balance_history: list[float]) -> float:

        if not balance_history:
            return 0.0

        return min(balance_history)

    @staticmethod
    def final(balance_history: list[float]) -> float:

        if not balance_history:
            return 0.0

        return balance_history[-1]