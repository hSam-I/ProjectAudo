from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):

    name = "mean_reversion"

    description = "Mean Reversion"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        close = last.get("close")
        upper = last.get("bb_upper")
        lower = last.get("bb_lower")
        rsi = last.get("rsi")

        if None in (close, upper, lower, rsi):
            return Signal.HOLD

        if close < lower and rsi < 30:
            return Signal.BUY

        if close > upper and rsi > 70:
            return Signal.SELL

        return Signal.HOLD