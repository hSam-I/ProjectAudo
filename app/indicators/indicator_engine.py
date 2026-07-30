import pandas as pd

from app.indicators.adx import ADX
from app.indicators.atr import ATR
from app.indicators.bollinger import BollingerBands
from app.indicators.cci import CCI
from app.indicators.ema import EMA
from app.indicators.macd import MACD
from app.indicators.obv import OBV
from app.indicators.rsi import RSI
from app.indicators.stochastic import Stochastic
from app.indicators.vwap import VWAP


class IndicatorEngine:
    """
    Central Indicator Engine.

    Responsible for calculating all technical indicators
    required by strategies, AI modules, optimizers,
    backtesting and reporting.
    """

    @staticmethod
    def prepare(
        df: pd.DataFrame,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_period: int = 14,
        atr_period: int = 14,
        adx_period: int = 14,
        bb_period: int = 20,
        bb_std: float = 2.0,
        stochastic_period: int = 14,
        stochastic_smooth: int = 3,
        cci_period: int = 20,
    ) -> pd.DataFrame:

        df = df.copy()

        # ==================================================
        # EMA
        # ==================================================

        df = EMA.calculate(
            df=df,
            period=ema_fast,
        )

        df = EMA.calculate(
            df=df,
            period=ema_slow,
        )

        df["ema_fast"] = df[f"ema_{ema_fast}"]
        df["ema_slow"] = df[f"ema_{ema_slow}"]

        # ==================================================
        # RSI
        # ==================================================

        df = RSI.calculate(
            df=df,
            period=rsi_period,
        )

        # ==================================================
        # ATR
        # ==================================================

        df = ATR.calculate(
            df=df,
            period=atr_period,
        )

        # ==================================================
        # MACD
        # ==================================================

        df = MACD.calculate(df)

        # ==================================================
        # ADX
        # ==================================================

        df = ADX.calculate(
            df=df,
            period=adx_period,
        )

        # ==================================================
        # Bollinger Bands
        # ==================================================

        df = BollingerBands.calculate(
            df=df,
            period=bb_period,
            std_multiplier=bb_std,
        )

        # ==================================================
        # VWAP
        # ==================================================

        df = VWAP.calculate(df)

        # ==================================================
        # OBV
        # ==================================================

        df = OBV.calculate(df)

        # ==================================================
        # CCI
        # ==================================================

        df = CCI.calculate(
            df=df,
            period=cci_period,
        )

        # ==================================================
        # Stochastic Oscillator
        # ==================================================

        df = Stochastic.calculate(
            df=df,
            period=stochastic_period,
            smooth=stochastic_smooth,
        )

        return df

    @staticmethod
    def calculate_all(
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Backward compatibility.

        Existing code can continue calling:

            IndicatorEngine.calculate_all(df)

        without any modification.
        """

        return IndicatorEngine.prepare(df)