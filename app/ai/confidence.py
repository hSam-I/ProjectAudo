from app.ai.scoring import MarketScore


class ConfidenceScore:
    """
    Converts market score into a confidence value.
    """

    @staticmethod
    def calculate(df) -> float:

        score = MarketScore.calculate(df)

        confidence = score / 3.0

        return round(confidence, 2)