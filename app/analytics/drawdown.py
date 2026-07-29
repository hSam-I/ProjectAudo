class DrawdownAnalyzer:
    """
    Calculates drawdown statistics.
    """

    @staticmethod
    def max_drawdown(balance_history: list[float]) -> float:

        if not balance_history:
            return 0.0

        peak = balance_history[0]
        max_dd = 0.0

        for balance in balance_history:

            if balance > peak:
                peak = balance

            drawdown = (peak - balance) / peak

            if drawdown > max_dd:
                max_dd = drawdown

        return round(max_dd * 100, 2)

    @staticmethod
    def current_drawdown(balance_history: list[float]) -> float:

        if not balance_history:
            return 0.0

        peak = max(balance_history)

        current = balance_history[-1]

        return round(((peak - current) / peak) * 100, 2)