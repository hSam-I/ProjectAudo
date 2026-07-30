import pandas as pd

from app.backtesting.backtest_runner import (
    BacktestRunner,
)


def test_backtest_runner():

    df = pd.DataFrame(
        {
            "close": list(range(1, 200)),
            "rsi": [60] * 199,
        }
    )

    df, strategy = BacktestRunner.prepare(
        df,
        {
            "ema_fast": 10,
            "ema_slow": 30,
        },
    )

    assert "ema_fast" in df.columns
    assert "ema_slow" in df.columns

    assert strategy.ema_fast == 10
    assert strategy.ema_slow == 30