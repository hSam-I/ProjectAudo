from app.indicators.ema import EMA
from app.indicators.rsi import RSI
from app.indicators.macd import MACD
from app.indicators.atr import ATR


class IndicatorEngine:

    @staticmethod
    def calculate_all(df):

        df = EMA.calculate(df, 20)
        df = EMA.calculate(df, 50)

        df = RSI.calculate(df)

        df = MACD.calculate(df)

        df = ATR.calculate(df)

        return df