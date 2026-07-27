from app.core.enums import Signal


class SignalFilter:
    """
    Filters strategy signals using the confidence score.
    """

    BUY_THRESHOLD = 60
    SELL_THRESHOLD = 60

    @classmethod
    def filter(
        cls,
        signal: Signal,
        score: int,
    ) -> Signal:

        if signal == Signal.BUY:
            return (
                Signal.BUY
                if score >= cls.BUY_THRESHOLD
                else Signal.HOLD
            )

        if signal == Signal.SELL:
            return (
                Signal.SELL
                if score >= cls.SELL_THRESHOLD
                else Signal.HOLD
            )

        return Signal.HOLD