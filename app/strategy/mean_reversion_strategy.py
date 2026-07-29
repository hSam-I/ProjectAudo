from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy

    BUY:
        RSI < 30

    SELL:
        RSI > 70

    Otherwise HOLD
    """

    name = "mean_reversion"

    description = "Mean Reversion Strategy"

    version = "1.0"

    def generate_signal(self, df):

        last = df.iloc[-1]

        rsi = last["rsi"]

        if rsi < 30:
            return Signal.BUY

        if rsi > 70:
            return Signal.SELL

        return Signal.HOLD