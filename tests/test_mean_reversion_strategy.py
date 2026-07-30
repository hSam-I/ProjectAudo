import pandas as pd

from app.core.enums import Signal
from app.strategy.mean_reversion_strategy import MeanReversionStrategy


def test_mean_reversion_buy():

    df = pd.DataFrame(
        [
            {
                "close": 95,
                "bb_lower": 100,
                "bb_upper": 120,
                "rsi": 25,
            }
        ]
    )

    strategy = MeanReversionStrategy()

    assert strategy.generate_signal(df) == Signal.BUY


def test_mean_reversion_sell():

    df = pd.DataFrame(
        [
            {
                "close": 125,
                "bb_lower": 100,
                "bb_upper": 120,
                "rsi": 75,
            }
        ]
    )

    strategy = MeanReversionStrategy()

    assert strategy.generate_signal(df) == Signal.SELL


def test_mean_reversion_hold():

    df = pd.DataFrame(
        [
            {
                "close": 110,
                "bb_lower": 100,
                "bb_upper": 120,
                "rsi": 50,
            }
        ]
    )

    strategy = MeanReversionStrategy()

    assert strategy.generate_signal(df) == Signal.HOLD