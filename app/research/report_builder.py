from datetime import UTC
from datetime import datetime


class ResearchReportBuilder:
    """
    Builds a structured research report
    from research engine outputs.
    """

    @staticmethod
    def build(results: dict) -> dict:

        return {
            "generated_at": datetime.now(
                UTC,
            ).isoformat(),

            "summary": {
                "risk_of_ruin": results["risk_of_ruin"],
                "survival_probability": results["survival_probability"],
                "average_result": results["average_result"],
                "best_result": results["best_result"],
                "worst_result": results["worst_result"],
            },

            "scenarios": {
                "count": results["scenario_count"],
            },

            "simulation_count": len(
                results["simulations"]
            ),
        }