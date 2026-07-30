import pandas as pd

from app.optimization.stress_test import StressTestEngine


class ScenarioRunner:
    """
    Runs predefined market scenarios.
    """

    def __init__(self):

        self.engine = StressTestEngine()

    def run(
        self,
        df: pd.DataFrame,
    ) -> dict:

        return {
            "normal": df.copy(),
            "flash_crash": self.engine.flash_crash(df),
            "bull_market": self.engine.rally(df),
            "high_volatility": self.engine.increase_volatility(df),
            "gap_down": self.engine.gap_down(df),
        }

    def scenario_names(self) -> list[str]:

        return [
            "normal",
            "flash_crash",
            "bull_market",
            "high_volatility",
            "gap_down",
        ]