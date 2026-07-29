import pandas as pd

from app.core.enums import Signal
from app.strategy.trend_following_strategy import TrendFollowingStrategy


def test_trend_following_buy():

    df = pd.DataFrame(
        [
            {
                "ema_20": 110,
                "ema_50": 100,
                "rsi": 60,
            }
        ]
    )

    strategy = TrendFollowingStrategy()

    assert strategy.generate_signal(df) == Signal.BUY


def test_trend_following_sell():

    df = pd.DataFrame(
        [
            {
                "ema_20": 90,
                "ema_50": 100,
                "rsi": 40,
            }
        ]
    )

    strategy = TrendFollowingStrategy()

    assert strategy.generate_signal(df) == Signal.SELL


def test_trend_following_hold():

    df = pd.DataFrame(
        [
            {
                "ema_20": 100,
                "ema_50": 100,
                "rsi": 50,
            }
        ]
    )

    strategy = TrendFollowingStrategy()

    assert strategy.generate_signal(df) == Signal.HOLD