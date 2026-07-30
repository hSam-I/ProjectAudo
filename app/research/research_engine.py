from app.optimization.optimization_pipeline import OptimizationPipeline
from app.optimization.scenario_runner import ScenarioRunner
from app.optimization.monte_carlo import MonteCarloSimulator
from app.optimization.risk_of_ruin import RiskOfRuinAnalyzer


class ResearchEngine:
    """
    Coordinates research modules and
    collects their outputs.
    """

    def __init__(self):

        self.pipeline = OptimizationPipeline()
        self.scenario_runner = ScenarioRunner()

    def run(
        self,
        profits: list[float],
        market_df,
    ) -> dict:

        monte_carlo = MonteCarloSimulator(
            profits,
        )

        simulations = monte_carlo.simulate(
            iterations=500,
        )

        risk = RiskOfRuinAnalyzer(
            simulations,
        )

        scenarios = self.scenario_runner.run(
            market_df,
        )

        return {
            "simulations": simulations,
            "scenario_count": len(scenarios),
            "average_result": monte_carlo.average_result(
                500,
            ),
            "best_result": monte_carlo.best_result(
                500,
            ),
            "worst_result": monte_carlo.worst_result(
                500,
            ),
            "risk_of_ruin": risk.ruin_probability(),
            "survival_probability": risk.survival_probability(),
        }