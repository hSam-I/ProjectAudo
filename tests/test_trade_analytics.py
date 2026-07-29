from app.analytics.trade_analytics import TradeAnalytics
from app.backtesting.trade import Trade
from app.core.enums import OrderSide


def test_trade_analytics():

    trade1 = Trade(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="2026",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    trade1.profit = 50

    trade2 = Trade(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="2026",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    trade2.profit = -20

    trades = [trade1, trade2]

    assert TradeAnalytics.total_profit(trades) == 30
    assert TradeAnalytics.winners(trades) == 1
    assert TradeAnalytics.losers(trades) == 1
    assert TradeAnalytics.win_rate(trades) == 50