from app.ai.features import FeatureExtractor


class MarketScore:
    """
    Produces a simple market score.
    """

    @staticmethod
    def calculate(df) -> float:

        features = FeatureExtractor.extract(df)

        score = 0

        if features["ema20"] > features["ema50"]:
            score += 1

        if features["rsi"] > 55:
            score += 1

        if features["atr"] > 0:
            score += 1

        return score