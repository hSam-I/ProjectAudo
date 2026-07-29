import pandas as pd

from app.ai.features import FeatureExtractor


class MarketScore:
    """
    Calculates a simple AI market quality score.
    """

    @staticmethod
    def calculate(df: pd.DataFrame) -> int:

        features = FeatureExtractor.extract(df)

        score = 0

        if features["ema20"] > features["ema50"]:
            score += 1

        if 45 <= features["rsi"] <= 65:
            score += 1

        if features["macd_histogram"] > 0:
            score += 1

        if features["atr"] > 0:
            score += 1

        return score