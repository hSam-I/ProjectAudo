import random


class MonteCarloSimulator:
    """
    Performs Monte Carlo simulations
    on historical trade profits.
    """

    def __init__(
        self,
        profits: list[float],
    ):

        self.profits = profits

    def simulate(
        self,
        iterations: int,
    ) -> list[float]:

        if not self.profits:
            return []

        simulations = []

        for _ in range(iterations):

            shuffled = random.sample(
                self.profits,
                len(self.profits),
            )

            simulations.append(
                sum(shuffled)
            )

        return simulations

    def average_result(
        self,
        iterations: int,
    ) -> float:

        results = self.simulate(
            iterations,
        )

        if not results:
            return 0.0

        return sum(results) / len(results)

    def best_result(
        self,
        iterations: int,
    ) -> float:

        results = self.simulate(
            iterations,
        )

        if not results:
            return 0.0

        return max(results)

    def worst_result(
        self,
        iterations: int,
    ) -> float:

        results = self.simulate(
            iterations,
        )

        if not results:
            return 0.0

        return min(results)