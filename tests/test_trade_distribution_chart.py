from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.reporting.trade_distribution_chart import TradeDistributionChart


def test_trade_distribution_chart(tmp_path):

    portfolio = Portfolio(10000)

    trade1 = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="1",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )
    trade1.profit = 10
    trade1.status = "CLOSED"

    trade2 = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="2",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )
    trade2.profit = -10
    trade2.status = "CLOSED"

    portfolio.trades = [trade1, trade2]

    chart = TradeDistributionChart()

    chart.filepath = tmp_path / "trade_distribution.png"

    chart.export(portfolio)

    assert chart.filepath.exists()


def test_trade_distribution_chart_no_trades(tmp_path):

    portfolio = Portfolio(10000)

    chart = TradeDistributionChart()

    chart.filepath = tmp_path / "trade_distribution.png"

    chart.export(portfolio)

    assert chart.filepath.exists()
    assert chart.filepath.stat().st_size > 0