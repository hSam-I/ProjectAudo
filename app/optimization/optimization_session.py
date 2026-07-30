from app.optimization.grid_search_optimizer import GridSearchOptimizer
from app.optimization.backtest_evaluator import BacktestEvaluator


class OptimizationSession:
    """
    Runs a complete optimization session.
    """

    def __init__(
        self,
        evaluator,
    ):

        self.evaluator = evaluator
        self.optimizer = GridSearchOptimizer()

    def run(
        self,
        parameter_sets: list[dict],
    ) -> dict:

        def evaluate(parameters):

            report = self.evaluator(parameters)

            return BacktestEvaluator.evaluate(
                report,
            )

        return self.optimizer.optimize(
            parameter_sets=parameter_sets,
            evaluator=evaluate,
        )