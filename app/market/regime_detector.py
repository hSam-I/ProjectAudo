import pandas as pd

from app.market.regime import MarketRegime


class MarketRegimeDetector:
    """
    Detects the current market regime.
    """

    @staticmethod
    def detect(
        df: pd.DataFrame,
    ) -> MarketRegime:

        last = df.iloc[-1]

        # -----------------------------
        # Breakout
        # -----------------------------

        if last["breakout"]:
            return MarketRegime.BREAKOUT

        # -----------------------------
        # Bull Trend
        # -----------------------------

        if last["trend_market"]:
            return MarketRegime.TRENDING_BULL

        # -----------------------------
        # Bear Trend
        # -----------------------------

        if last["bear_market"]:
            return MarketRegime.TRENDING_BEAR

        # -----------------------------
        # Sideways
        # -----------------------------

        if last["sideways_market"]:
            return MarketRegime.RANGING

        # -----------------------------
        # High Volatility
        # -----------------------------

        if last["high_volatility_market"]:
            return MarketRegime.HIGH_VOLATILITY

        # -----------------------------
        # Low Volatility
        # -----------------------------

        if last["low_volatility_market"]:
            return MarketRegime.LOW_VOLATILITY

        return MarketRegime.UNKNOWN