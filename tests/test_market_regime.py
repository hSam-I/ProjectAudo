import pandas as pd

from app.ai.market_regime import MarketRegime


def test_market_regime_trend():

    df = pd.DataFrame(
        [
            {
                "ema_20": 110,
                "ema_50": 100,
            }
        ]
    )

    assert MarketRegime.detect(df) == MarketRegime.TREND


def test_market_regime_range():

    df = pd.DataFrame(
        [
            {
                "ema_20": 100.5,
                "ema_50": 100,
            }
        ]
    )

    assert MarketRegime.detect(df) == MarketRegime.RANGE


def test_market_regime_breakout():

    df = pd.DataFrame(
        [
            {
                "ema_20": 102,
                "ema_50": 100,
            }
        ]
    )

    assert MarketRegime.detect(df) == MarketRegime.BREAKOUT