import pandas as pd

from app.strategy.breakout_strategy import BreakoutStrategy


def test_breakout_buy():

    rows = []

    for i in range(20):
        rows.append(
            {
                "high": 100 + i,
                "low": 90 + i,
                "close": 95 + i,
            }
        )

    rows.append(
        {
            "high": 125,
            "low": 118,
            "close": 130,
        }
    )

    df = pd.DataFrame(rows)

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == "BUY"


def test_breakout_sell():

    rows = []

    for i in range(20):
        rows.append(
            {
                "high": 120 + i,
                "low": 100 + i,
                "close": 110 + i,
            }
        )

    rows.append(
        {
            "high": 118,
            "low": 80,
            "close": 79,
        }
    )

    df = pd.DataFrame(rows)

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == "SELL"


def test_breakout_hold():

    rows = []

    for i in range(21):
        rows.append(
            {
                "high": 100,
                "low": 90,
                "close": 95,
            }
        )

    df = pd.DataFrame(rows)

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == "HOLD"