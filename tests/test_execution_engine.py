import pytest

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

    assert portfolio.closed_trades_count == 1


def test_execution_engine_applies_fee_to_balance():

    portfolio = Portfolio(10000)

    engine = ExecutionEngine(
        portfolio=portfolio,
        fee_model=FeeModel(fee_rate=0.01),
        slippage_model=SlippageModel(slippage_rate=0.0),
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

    # 1% fee on a $100 entry: balance drops by exactly $1.
    assert portfolio.balance == 9999.0

    trade.close(
        exit_price=110,
        exit_time="2026-01-02",
        reason="TP",
    )

    engine.execute_sell(trade)

    # Entry fee ($1) + exit fee (1% of $110 = $1.10) + $10 profit.
    assert portfolio.balance == 10000 - 1 - 1.10 + 10


def test_execution_engine_applies_slippage_to_prices_and_profit():

    portfolio = Portfolio(10000)

    engine = ExecutionEngine(
        portfolio=portfolio,
        fee_model=FeeModel(fee_rate=0.0),
        slippage_model=SlippageModel(slippage_rate=0.01),
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

    # Buys fill worse than market: +1% slippage on entry.
    assert trade.entry_price == 101.0

    trade.close(
        exit_price=110,
        exit_time="2026-01-02",
        reason="TP",
    )

    engine.execute_sell(trade)

    # Sells fill worse than market too: -1% slippage on exit.
    assert trade.exit_price == 108.9

    # Regression: profit must reflect the slippage-adjusted exit
    # price, not the pre-slippage price passed to close().
    assert trade.profit == pytest.approx(108.9 - 101.0)

    assert portfolio.balance == pytest.approx(10000 + (108.9 - 101.0))