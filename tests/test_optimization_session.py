from app.optimization.optimization_session import (
    OptimizationSession,
)


def fake_backtest(parameters):

    return {
        "profit_factor": parameters["ema_fast"] / 10,
        "win_rate": 60,
        "max_drawdown": 8,
        "expectancy": 12,
    }


def test_optimization_session():

    session = OptimizationSession(
        evaluator=fake_backtest,
    )

    best = session.run(
        [
            {"ema_fast": 10},
            {"ema_fast": 20},
            {"ema_fast": 30},
        ]
    )

    assert best["parameters"]["ema_fast"] == 30
    assert best["metrics"]["profit_factor"] == 3.0