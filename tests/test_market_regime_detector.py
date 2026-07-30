import pandas as pd

from app.market.regime import MarketRegime
from app.market.regime_detector import (
    MarketRegimeDetector,
)


def test_market_regime_detector():

    df = pd.DataFrame(
        {
            "trend_market": [True],
            "bear_market": [False],
            "sideways_market": [False],
            "high_volatility_market": [False],
            "low_volatility_market": [False],
            "breakout": [False],
        }
    )

    regime = MarketRegimeDetector.detect(df)

    assert regime == MarketRegime.TRENDING_BULL