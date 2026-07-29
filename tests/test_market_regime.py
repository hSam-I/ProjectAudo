from app.ai.market_regime import (
    MarketRegime,
    MarketRegimeDetector,
)


def test_market_regime():

    detector = MarketRegimeDetector()

    regime = detector.detect(None)

    assert regime == MarketRegime.TRENDING