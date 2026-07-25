import pandas as pd

from app.strategy.base_strategy import BaseStrategy


class EMARSIStrategy(BaseStrategy):

    def generate_signal(self, df: pd.DataFrame) -> str:

        last = df.iloc[-1]

        ema20 = last["ema_20"]
        ema50 = last["ema_50"]
        rsi = last["rsi"]

        if ema20 > ema50 and rsi < 30:
            return "BUY"

        elif ema20 < ema50 and rsi > 70:
            return "SELL"

        return "HOLD"