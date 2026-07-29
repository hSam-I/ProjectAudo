from app.ai.market_regime import MarketRegime
from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.ema_rsi_strategy import EMARSIStrategy


class StrategySelector:
    """
    Dynamically selects the best strategy.
    """

    @staticmethod
    def choose(df):
        """
        Returns the strategy name.
        """

        regime = MarketRegime.detect(df)

        if regime == "bull":
            return "ema_rsi"

        if regime == "sideways":
            return "breakout"

        if regime == "volatile":
            return "breakout"

        return "ema_rsi"

    @staticmethod
    def select(df):
        """
        Returns a strategy instance.
        """

        regime = MarketRegime.detect(df)

        if regime == "bull":
            return EMARSIStrategy()

        if regime == "sideways":
            return BreakoutStrategy()

        if regime == "volatile":
            return BreakoutStrategy()

        return EMARSIStrategy()