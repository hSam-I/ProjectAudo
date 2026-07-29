from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend Following Strategy

    Long:
        EMA20 > EMA50
        RSI > 55

    Short:
        EMA20 < EMA50
        RSI < 45
    """

    name = "trend_following"

    description = "Trend Following Strategy"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        ema20 = last["ema_20"]
        ema50 = last["ema_50"]
        rsi = last["rsi"]

        if ema20 > ema50 and rsi > 55:
            return Signal.BUY

        if ema20 < ema50 and rsi < 45:
            return Signal.SELL

        return Signal.HOLD