from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class SwingStrategy(BaseStrategy):

    name = "swing"

    description = "Swing Strategy"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        if (
            last["ema_fast"] > last["ema_slow"]
            and last["macd"] > 0
            and last["adx"] > 25
        ):
            return Signal.BUY

        if (
            last["ema_fast"] < last["ema_slow"]
            and last["macd"] < 0
            and last["adx"] > 25
        ):
            return Signal.SELL

        return Signal.HOLD