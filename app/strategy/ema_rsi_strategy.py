from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class EMARSIStrategy(BaseStrategy):
    """
    EMA20 / EMA50 crossover strategy confirmed by RSI.
    """

    name = "ema_rsi"

    description = "EMA crossover confirmed by RSI."

    version = "1.0"

    def generate_signal(self, df) -> Signal:

        if len(df) < 2:
            return Signal.HOLD

        previous = df.iloc[-2]
        current = df.iloc[-1]

        prev_ema20 = previous["ema_20"]
        prev_ema50 = previous["ema_50"]

        ema20 = current["ema_20"]
        ema50 = current["ema_50"]

        rsi = current["rsi"]

        if (
            prev_ema20 <= prev_ema50
            and ema20 > ema50
            and rsi < 70
        ):
            return Signal.BUY

        if (
            prev_ema20 >= prev_ema50
            and ema20 < ema50
            and rsi > 30
        ):
            return Signal.SELL

        return Signal.HOLD