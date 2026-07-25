from app.indicators.ema import EMA
from app.indicators.rsi import RSI
from app.indicators.macd import MACD


class IndicatorEngine:

    @staticmethod
    def calculate_all(df):

        df = EMA.calculate(df, 20)
        df = EMA.calculate(df, 50)

        df = RSI.calculate(df)

        df = MACD.calculate(df)

        return df