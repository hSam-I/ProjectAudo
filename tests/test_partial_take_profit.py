from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.risk.partial_take_profit import PartialTakeProfit


def test_partial_take_profit():

    trade = Trade(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        entry_price=100,
        quantity=2,
        entry_time="1",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    PartialTakeProfit.update(
        trade,
        current_price=105,
    )

    assert trade.partial_tp_taken is True

    assert trade.remaining_quantity == 1