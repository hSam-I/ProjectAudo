from enum import StrEnum


class MarketRegime(StrEnum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"


class MarketRegimeDetector:
    """
    Detects current market regime.
    """

    def detect(self, df) -> MarketRegime:

        return MarketRegime.TRENDING