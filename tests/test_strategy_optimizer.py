import pandas as pd

from app.optimization.optimizer import StrategyOptimizer


def test_strategy_optimizer():

    df = pd.DataFrame({
        "close": range(500)
    })

    optimizer = StrategyOptimizer()

    params = {
        "ema_fast": [10, 20],
        "ema_slow": [50, 100],
        "rsi": [30, 35],
    }

    combinations = optimizer.generate_parameter_grid(params)

    assert len(combinations) == 8