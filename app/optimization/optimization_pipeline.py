class OptimizationPipeline:
    """
    Stores optimization results and
    returns the best one.
    """

    def __init__(self):

        self.results = []

    def add_result(
        self,
        parameters: dict,
        metrics: dict,
    ) -> None:

        self.results.append(
            {
                "parameters": parameters,
                "metrics": metrics,
            }
        )

    def best(self):

        if not self.results:
            raise ValueError(
                "No optimization results."
            )

        return max(
            self.results,
            key=lambda result: result["metrics"]["profit_factor"],
        )