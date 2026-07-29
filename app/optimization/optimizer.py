from itertools import product


class StrategyOptimizer:
    """
    Generates parameter combinations
    for strategy optimization.
    """

    def generate_parameter_grid(
        self,
        parameters: dict,
    ):

        keys = list(parameters.keys())

        values = list(parameters.values())

        combinations = []

        for combination in product(*values):

            combinations.append(
                dict(
                    zip(
                        keys,
                        combination,
                    )
                )
            )

        return combinations

    def best_result(
        self,
        results: list[dict],
    ) -> dict:

        return max(
            results,
            key=lambda x: x["profit_factor"],
        )