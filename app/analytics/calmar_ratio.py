class CalmarRatio:
    """
    Calculates Calmar Ratio.
    """

    @staticmethod
    def calculate(
        annual_return: float,
        max_drawdown: float,
    ) -> float:

        if max_drawdown == 0:
            return 0.0

        return round(
            annual_return / max_drawdown,
            2,
        )