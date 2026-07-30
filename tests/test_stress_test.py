import pandas as pd

from app.optimization.stress_test import StressTestEngine


def test_flash_crash():

    df = pd.DataFrame(
        {
            "close": [100],
            "atr": [2],
        }
    )

    engine = StressTestEngine()

    stressed = engine.flash_crash(
        df,
        percent=0.30,
    )

    assert stressed.iloc[0]["close"] == 70


def test_rally():

    df = pd.DataFrame(
        {
            "close": [100],
            "atr": [2],
        }
    )

    engine = StressTestEngine()

    stressed = engine.rally(
        df,
        percent=0.20,
    )

    assert stressed.iloc[0]["close"] == 120


def test_volatility():

    df = pd.DataFrame(
        {
            "close": [100],
            "atr": [2],
        }
    )

    engine = StressTestEngine()

    stressed = engine.increase_volatility(
        df,
        multiplier=3,
    )

    assert stressed.iloc[0]["atr"] == 6


def test_gap_down():

    df = pd.DataFrame(
        {
            "close": [100],
            "atr": [2],
        }
    )

    engine = StressTestEngine()

    stressed = engine.gap_down(
        df,
        percent=0.10,
    )

    assert stressed.iloc[0]["close"] == 90