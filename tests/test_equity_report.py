from app.backtesting.portfolio import Portfolio
from app.reporting.equity_report import EquityReport


def test_equity_report_export(tmp_path):

    portfolio = Portfolio(10000)

    portfolio.balance_history = [
        10000,
        10100,
        9950,
        10250,
    ]

    report = EquityReport()

    report.filepath = tmp_path / "equity_curve.csv"

    report.export(portfolio)

    assert report.filepath.exists()

    content = report.filepath.read_text()

    assert "Trade" in content
    assert "Balance" in content
    assert "10250" in content