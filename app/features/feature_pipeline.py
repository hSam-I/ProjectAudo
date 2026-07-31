from app.features.feature_engine import FeatureEngine

from app.indicators.adx import ADX
from app.indicators.atr import ATR
from app.indicators.bollinger import BollingerBands
from app.indicators.cci import CCI
from app.indicators.ema import EMA
from app.indicators.ichimoku import Ichimoku
from app.indicators.macd import MACD
from app.indicators.obv import OBV
from app.indicators.rsi import RSI
from app.indicators.stochastic import Stochastic
from app.indicators.vwap import VWAP


class FeaturePipeline:

    @staticmethod
    def build(
        df,
        ema_fast=20,
        ema_slow=50,
    ):

        df = EMA.calculate(df, ema_fast)
        df = EMA.calculate(df, ema_slow)

        df["ema_fast"] = df[f"ema_{ema_fast}"]
        df["ema_slow"] = df[f"ema_{ema_slow}"]

        df = RSI.calculate(df)
        df = ATR.calculate(df)
        df = MACD.calculate(df)
        df = ADX.calculate(df)
        df = BollingerBands.calculate(df)
        df = VWAP.calculate(df)
        df = OBV.calculate(df)
        df = CCI.calculate(df)
        df = Ichimoku.calculate(df)
        df = Stochastic.calculate(df)

        # -------------------------------
        # AI FEATURES
        # -------------------------------

        df = FeatureEngine.build(df)

        return df