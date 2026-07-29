from app.ai.market_regime import (
    MarketRegime,
    MarketRegimeDetector,
)


class StrategySelector:
    """
    Chooses the best strategy
    according to the market regime.
    """

    def __init__(self):

        self.detector = MarketRegimeDetector()

    def select(self, df) -> str:

        regime = self.detector.detect(df)

        if regime == MarketRegime.TRENDING:
            return "ema_rsi"

        if regime == MarketRegime.RANGING:
            return "bollinger"

        if regime == MarketRegime.VOLATILE:
            return "breakout"

        return "ema_rsi"