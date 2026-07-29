class OptimizationRunner:
    """
    Executes optimization runs and
    selects the best result.
    """

    def select_best(
        self,
        results: list[dict],
    ) -> dict:

        if not results:
            raise ValueError(
                "No optimization results."
            )

        return max(
            results,
            key=lambda x: x["profit_factor"],
        )