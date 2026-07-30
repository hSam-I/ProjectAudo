from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class ScalpingStrategy(BaseStrategy):

    name = "scalping"

    description = "Scalping Strategy"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        if (
            last["macd"] > last["macd_signal"]
            and last["rsi"] > 55
        ):
            return Signal.BUY

        if (
            last["macd"] < last["macd_signal"]
            and last["rsi"] < 45
        ):
            return Signal.SELL

        return Signal.HOLD