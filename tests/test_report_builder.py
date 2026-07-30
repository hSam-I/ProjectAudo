from app.backtesting.portfolio import Portfolio
from app.reporting.report_builder import ReportBuilder
from app.research.report_builder import ResearchReportBuilder


def test_report_builder():

    portfolio = Portfolio(10000)

    report = ReportBuilder.build(portfolio)

    assert report.total_trades == 0

    assert report.win_rate == 0

    assert report.expectancy == 0

    from app.research.report_builder import ResearchReportBuilder


def test_research_report_builder():

    results = {
        "risk_of_ruin": 0.15,
        "survival_probability": 0.85,
        "average_result": 135.4,
        "best_result": 420,
        "worst_result": -210,
        "scenario_count": 5,
        "simulations": [1, 2, 3, 4],
    }

    report = ResearchReportBuilder.build(results)

    assert report["summary"]["risk_of_ruin"] == 0.15
    assert report["summary"]["survival_probability"] == 0.85
    assert report["simulation_count"] == 4
    assert report["scenarios"]["count"] == 5