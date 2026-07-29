from app.ai.confidence import ConfidenceScore


class TradeFilter:
    """
    Rejects weak AI signals.
    """

    MIN_CONFIDENCE = 0.60

    @classmethod
    def should_trade(cls, df) -> bool:

        confidence = ConfidenceScore.calculate(df)

        return confidence >= cls.MIN_CONFIDENCE