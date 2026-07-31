from app.ai.market_regime import MarketRegime
from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy


class StrategySelector:

    @staticmethod
    def choose(df):

        regime = MarketRegime.detect(df)

        if regime == MarketRegime.TREND:
            return "ema_rsi"

        if regime == MarketRegime.RANGE:
            return "breakout"

        if regime == MarketRegime.BREAKOUT:
            return "breakout"

        return "ema_rsi"

    @staticmethod
    def select(df):

        regime = MarketRegime.detect(df)

        if regime == MarketRegime.TREND:
            return EMARSIStrategy()

        if regime == MarketRegime.RANGE:
            return BreakoutStrategy()

        if regime == MarketRegime.BREAKOUT:
            return BreakoutStrategy()

        return EMARSIStrategy()