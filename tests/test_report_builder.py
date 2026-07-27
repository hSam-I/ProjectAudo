from app.backtesting.portfolio import Portfolio
from app.reporting.report_builder import ReportBuilder


def test_report_builder():

    portfolio = Portfolio(10000)

    report = ReportBuilder.build(portfolio)

    assert report.total_trades == 0

    assert report.win_rate == 0

    assert report.expectancy == 0