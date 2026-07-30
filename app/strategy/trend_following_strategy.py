from app.core.enums import Signal
from app.strategy.base_strategy import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend Following Strategy

    Long:
        EMA Fast > EMA Slow
        RSI > RSI Buy

    Short:
        EMA Fast < EMA Slow
        RSI < RSI Sell
    """

    name = "trend_following"

    description = "Trend Following Strategy"

    version = "2.0"

    def __init__(
        self,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_buy: float = 55,
        rsi_sell: float = 45,
    ):

        self.ema_fast = ema_fast
        self.ema_slow = ema_slow

        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signal(
        self,
        df,
    ):

        last = df.iloc[-1]

        # Yeni IndicatorEngine kullanıldıysa
        if "ema_fast" in last.index:
            ema_fast = last["ema_fast"]
        else:
            ema_fast = last[f"ema_{self.ema_fast}"]

        if "ema_slow" in last.index:
            ema_slow = last["ema_slow"]
        else:
            ema_slow = last[f"ema_{self.ema_slow}"]

        rsi = last["rsi"]

        if (
            ema_fast > ema_slow
            and rsi > self.rsi_buy
        ):
            return Signal.BUY

        if (
            ema_fast < ema_slow
            and rsi < self.rsi_sell
        ):
            return Signal.SELL

        return Signal.HOLD