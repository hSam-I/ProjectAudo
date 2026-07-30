class RiskOfRuinAnalyzer:
    """
    Estimates the probability of
    losing all trading capital.
    """

    def __init__(
        self,
        simulations: list[float],
    ):

        self.simulations = simulations

    def ruin_probability(self) -> float:

        if not self.simulations:
            return 0.0

        ruined = sum(
            1
            for value in self.simulations
            if value <= 0
        )

        return ruined / len(self.simulations)

    def survival_probability(self) -> float:

        return (
            1.0
            - self.ruin_probability()
        )

    def worst_case(self) -> float:

        if not self.simulations:
            return 0.0

        return min(self.simulations)

    def best_case(self) -> float:

        if not self.simulations:
            return 0.0

        return max(self.simulations)

    def average(self) -> float:

        if not self.simulations:
            return 0.0

        return (
            sum(self.simulations)
            / len(self.simulations)
        )