from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide


def test_multiple_open_positions():

    portfolio = Portfolio(10000)

    t1 = Trade(
        symbol="BTC",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=1,
        entry_time="1",
        stop_loss=90,
        take_profit=120,
        risk_amount=100,
    )

    t2 = Trade(
        symbol="ETH",
        side=OrderSide.BUY,
        entry_price=200,
        quantity=1,
        entry_time="2",
        stop_loss=180,
        take_profit=240,
        risk_amount=100,
    )

    portfolio.open_trade(t1)
    portfolio.open_trade(t2)

    assert portfolio.open_trades == 2