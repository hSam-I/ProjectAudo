import pandas as pd

from app.market.regime import MarketRegime


class MarketRegimeDetector:

    @staticmethod
    def detect(
        df: pd.DataFrame,
    ) -> MarketRegime:

        last = df.iloc[-1]

        if last.get("breakout", False):
            return MarketRegime.BREAKOUT

        if last.get("trend_market", False):
            return MarketRegime.TRENDING_BULL

        if last.get("bear_market", False):
            return MarketRegime.TRENDING_BEAR

        if last.get("sideways_market", False):
            return MarketRegime.RANGING

        if last.get("high_volatility_market", False):
            return MarketRegime.HIGH_VOLATILITY

        if last.get("low_volatility_market", False):
            return MarketRegime.LOW_VOLATILITY

        return MarketRegime.UNKNOWN