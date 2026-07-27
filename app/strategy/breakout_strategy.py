from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class BreakoutStrategy(BaseStrategy):
    """
    Simple breakout strategy.
    """

    name = "breakout"

    description = "Simple breakout strategy."

    version = "1.0"

    def generate_signal(self, df) -> Signal:

        if len(df) < 2:
            return Signal.HOLD

        previous = df.iloc[-2]
        current = df.iloc[-1]

        if current["close"] > previous["high"]:
            return Signal.BUY

        if current["close"] < previous["low"]:
            return Signal.SELL

        return Signal.HOLD