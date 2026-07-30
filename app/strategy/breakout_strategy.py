from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class BreakoutStrategy(BaseStrategy):

    name = "breakout"

    description = "Breakout Strategy"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        breakout = last.get("breakout", False)
        breakdown = last.get("breakdown", False)

        if breakout:
            return Signal.BUY

        if breakdown:
            return Signal.SELL

        return Signal.HOLD