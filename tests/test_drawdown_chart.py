from app.backtesting.portfolio import Portfolio
from app.reporting.drawdown_chart import DrawdownChart


def test_drawdown_chart_export(tmp_path):

    portfolio = Portfolio(10000)

    portfolio.balance_history = [
        10000,
        10200,
        10100,
        9800,
        10400,
    ]

    chart = DrawdownChart()

    chart.filepath = tmp_path / "drawdown.png"

    chart.export(portfolio)

    assert chart.filepath.exists()