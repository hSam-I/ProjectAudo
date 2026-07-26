from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.broker.execution_engine import ExecutionEngine
from app.broker.fee_model import FeeModel
from app.broker.slippage_model import SlippageModel
from app.execution.order_book import OrderBook


def test_execution_engine():

    portfolio = Portfolio(10000)

    engine = ExecutionEngine(
        portfolio=portfolio,
        fee_model=FeeModel(),
        slippage_model=SlippageModel(),
        order_book=OrderBook(),
    )

    trade = Trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100,
        quantity=1,
        entry_time="2026-01-01",
        stop_loss=95,
        take_profit=110,
        risk_amount=100,
    )

    engine.execute_buy(trade)

    assert portfolio.total_trades == 1

    trade.close(
        exit_price=110,
        exit_time="2026-01-02",
        reason="TP",
    )

    engine.execute_sell(trade)

    assert portfolio.closed_trades == 1