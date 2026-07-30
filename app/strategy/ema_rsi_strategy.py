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

        prev_ema_fast = previous["ema_fast"]
        prev_ema_slow = previous["ema_slow"]

        ema_fast = current["ema_fast"]
        ema_slow = current["ema_slow"]

        rsi = current["rsi"]

        if (
            prev_ema_fast <= prev_ema_slow
            and ema_fast > ema_slow
            and rsi < 70
        ):
            return Signal.BUY

        if (
            prev_ema_fast >= prev_ema_slow
            and ema_fast < ema_slow
            and rsi > 30
        ):
            return Signal.SELL

        return Signal.HOLD