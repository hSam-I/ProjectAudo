from app.market.regime import MarketRegime

from app.strategy.breakout_strategy import BreakoutStrategy
from app.strategy.mean_reversion_strategy import MeanReversionStrategy
from app.strategy.scalping_strategy import ScalpingStrategy
from app.strategy.swing_strategy import SwingStrategy
from app.strategy.trend_following_strategy import TrendFollowingStrategy


class StrategySelectorV2:

    @staticmethod
    def choose(regime):

        if regime == MarketRegime.TRENDING_BULL:
            return TrendFollowingStrategy()

        if regime == MarketRegime.TRENDING_BEAR:
            return TrendFollowingStrategy()

        if regime == MarketRegime.RANGING:
            return MeanReversionStrategy()

        if regime == MarketRegime.BREAKOUT:
            return BreakoutStrategy()

        if regime == MarketRegime.HIGH_VOLATILITY:
            return ScalpingStrategy()

        if regime == MarketRegime.LOW_VOLATILITY:
            return SwingStrategy()

        return TrendFollowingStrategy()