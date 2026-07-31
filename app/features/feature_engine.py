import pandas as pd

from app.features.market_features import MarketFeatures
from app.features.momentum_features import MomentumFeatures
from app.features.pattern_features import PatternFeatures
from app.features.trend_features import TrendFeatures
from app.features.volatility_features import VolatilityFeatures
from app.features.volume_features import VolumeFeatures


class FeatureEngine:
    """
    Builds every AI feature used
    inside Project Audo.
    """

    @staticmethod
    def build(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        # ----------------------------------------
        # Trend
        # ----------------------------------------

        df = TrendFeatures.build(df)

        # ----------------------------------------
        # Momentum
        # ----------------------------------------

        df = MomentumFeatures.build(df)

        # ----------------------------------------
        # Volatility
        # ----------------------------------------

        df = VolatilityFeatures.build(df)

        # ----------------------------------------
        # Volume
        # ----------------------------------------

        df = VolumeFeatures.build(df)

        # ----------------------------------------
        # Pattern
        # ----------------------------------------

        df = PatternFeatures.build(df)

        # ----------------------------------------
        # Market
        # ----------------------------------------

        df = MarketFeatures.build(df)

        # ----------------------------------------
        # Compatibility aliases
        # ----------------------------------------

        if "trend_up" in df.columns:
            df["trend_market"] = df["trend_up"]

        if "strong_trend" in df.columns:
            df["trend_strength_ok"] = df["strong_trend"]

        return df