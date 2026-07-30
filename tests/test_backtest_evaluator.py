from app.optimization.backtest_evaluator import (
    BacktestEvaluator,
)


def test_backtest_evaluator():

    report = {
        "profit_factor": 2.15,
        "win_rate": 61.5,
        "max_drawdown": 8.2,
        "expectancy": 14.8,
    }

    metrics = BacktestEvaluator.evaluate(
        report,
    )

    assert metrics["profit_factor"] == 2.15
    assert metrics["win_rate"] == 61.5
    assert metrics["max_drawdown"] == 8.2
    assert metrics["expectancy"] == 14.8