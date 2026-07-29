import pandas as pd

from app.core.enums import Signal
from app.strategy.mean_reversion_strategy import MeanReversionStrategy


def test_mean_reversion_buy():

    df = pd.DataFrame(
        [
            {
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
                "rsi": 50,
            }
        ]
    )

    strategy = MeanReversionStrategy()

    assert strategy.generate_signal(df) == Signal.HOLD