from app.backtesting.portfolio import Portfolio
from app.reporting.equity_chart import EquityChart


def test_equity_chart_export(tmp_path):

    portfolio = Portfolio(10000)

    portfolio.balance_history = [
        10000,
        10150,
        10020,
        10280,
    ]

    chart = EquityChart()

    chart.filepath = tmp_path / "equity_curve.png"

    chart.export(portfolio)

    assert chart.filepath.exists()