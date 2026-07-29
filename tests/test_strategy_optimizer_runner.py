import pandas as pd

from app.optimization.optimizer import StrategyOptimizer


def test_optimizer_best_result():

    df = pd.DataFrame({
        "close": range(500)
    })

    optimizer = StrategyOptimizer()

    fake_results = [
        {
            "parameters": {
                "ema_fast": 10,
                "ema_slow": 50,
            },
            "profit_factor": 1.20,
        },
        {
            "parameters": {
                "ema_fast": 20,
                "ema_slow": 100,
            },
            "profit_factor": 2.15,
        },
    ]

    best = optimizer.best_result(fake_results)

    assert best["profit_factor"] == 2.15