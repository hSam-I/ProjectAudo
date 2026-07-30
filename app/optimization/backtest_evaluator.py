class BacktestEvaluator:
    """
    Converts a backtest result into
    optimization metrics.
    """

    @staticmethod
    def evaluate(report: dict) -> dict:

        return {
            "profit_factor": report.get(
                "profit_factor",
                0.0,
            ),
            "win_rate": report.get(
                "win_rate",
                0.0,
            ),
            "max_drawdown": report.get(
                "max_drawdown",
                0.0,
            ),
            "expectancy": report.get(
                "expectancy",
                0.0,
            ),
        }