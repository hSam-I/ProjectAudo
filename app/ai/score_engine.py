import pandas as pd

from app.ai.weights import FEATURE_WEIGHTS


class ScoreEngine:
    """
    AI Feature Scoring Engine.
    """

    @staticmethod
    def score(
        df: pd.DataFrame,
    ):

        last = df.iloc[-1]

        score = 0
        reasons = []

        for feature, weight in FEATURE_WEIGHTS.items():

            if feature not in last.index:
                continue

            value = last[feature]

            if bool(value):
                score += weight
                reasons.append(feature)

        return score, reasons