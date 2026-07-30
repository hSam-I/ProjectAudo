from app.optimization.optimization_pipeline import OptimizationPipeline


class GridSearchOptimizer:
    """
    Performs a simple grid search over
    strategy parameters.
    """

    def __init__(self):

        self.pipeline = OptimizationPipeline()

    def optimize(
        self,
        parameter_sets: list[dict],
        evaluator,
    ) -> dict:

        for parameters in parameter_sets:

            metrics = evaluator(parameters)

            self.pipeline.add_result(
                parameters=parameters,
                metrics=metrics,
            )

        return self.pipeline.best()