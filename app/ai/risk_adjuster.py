from app.ai.confidence import ConfidenceScore


class RiskAdjuster:
    """
    Adjusts risk based on AI confidence.
    """

    @staticmethod
    def adjusted_risk(
        df,
        base_risk: float,
    ) -> float:

        confidence = ConfidenceScore.calculate(df)

        if confidence >= 0.90:
            return base_risk

        if confidence >= 0.75:
            return round(base_risk * 0.75, 4)

        if confidence >= 0.50:
            return round(base_risk * 0.50, 4)

        return 0.0