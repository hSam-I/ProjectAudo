from app.backtesting.performance_report import PerformanceReport
from app.backtesting.trade import Trade
from app.core.enums import OrderSide


def test_performance_report():

    trades = [

        Trade(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            entry_price=100,
            quantity=1,
            entry_time="2026-01-01",
            stop_loss=95,
            take_profit=110,
            risk_amount=10,
            exit_price=110,
            exit_time="2026-01-01",
            status="CLOSED",
            profit=10,
        ),

        Trade(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            entry_price=100,
            quantity=1,
            entry_time="2026-01-02",
            stop_loss=95,
            take_profit=110,
            risk_amount=10,
            exit_price=95,
            exit_time="2026-01-02",
            status="CLOSED",
            profit=-5,
        ),
    ]

    report = PerformanceReport.generate(trades)

    assert report["total_trades"] == 2
    assert report["net_profit"] == 5
    assert report["gross_profit"] == 10
    assert report["gross_loss"] == 5
    assert report["profit_factor"] == 2