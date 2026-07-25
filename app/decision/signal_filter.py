class SignalFilter:
    """
    Filters strategy signals using the confidence score.

    Strategy generates the candidate signal.
    SignalScorer evaluates its quality.
    SignalFilter decides whether the signal
    is strong enough to execute.
    """

    BUY_THRESHOLD = 60
    SELL_THRESHOLD = 60

    @classmethod
    def filter(cls, signal: str, score: int) -> str:

        if signal == "BUY":
            return "BUY" if score >= cls.BUY_THRESHOLD else "HOLD"

        if signal == "SELL":
            return "SELL" if score >= cls.SELL_THRESHOLD else "HOLD"

        return "HOLD"