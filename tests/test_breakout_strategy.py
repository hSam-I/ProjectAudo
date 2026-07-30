import pandas as pd

from app.core.enums import Signal
from app.strategy.breakout_strategy import BreakoutStrategy


def test_breakout_buy():

    df = pd.DataFrame(
        [
            {
                "breakout": True,
                "breakdown": False,
            }
        ]
    )

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == Signal.BUY


def test_breakout_sell():

    df = pd.DataFrame(
        [
            {
                "breakout": False,
                "breakdown": True,
            }
        ]
    )

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == Signal.SELL


def test_breakout_hold():

    df = pd.DataFrame(
        [
            {
                "breakout": False,
                "breakdown": False,
            }
        ]
    )

    strategy = BreakoutStrategy()

    assert strategy.generate_signal(df) == Signal.HOLD