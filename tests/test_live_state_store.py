"""
Covers Phase 2 of the live-paper-trading work:
app.execution.live_state_store.LiveStateStore.

The critical invariant tested here is restore_into() mutating the
given Portfolio/PortfolioManager IN PLACE rather than replacing them -
Backtester's PaperBroker holds a reference to the exact Portfolio
object passed to it at construction time, so swapping that reference
out (instead of mutating its attributes) would silently disconnect the
broker from the restored state.
"""

import os

from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.execution.live_state_store import LiveStateStore
from app.portfolio.portfolio_manager import PortfolioManager


def _open_trade(symbol="BTC/USDT", profit=0.0, status="OPEN"):

    trade = Trade(
        symbol=symbol,
        side=OrderSide.BUY,
        entry_price=100.0,
        quantity=1.0,
        entry_time="2024-01-01 00:00:00",
        stop_loss=95.0,
        take_profit=110.0,
        risk_amount=50.0,
    )

    if status == "CLOSED":
        trade.close(exit_price=105.0, exit_time="2024-01-01 05:00:00")

    return trade


def test_load_returns_none_when_no_file_exists(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    assert LiveStateStore.load() is None


def test_restore_into_returns_none_when_no_saved_state(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    portfolio = Portfolio(10000)
    portfolio_manager = PortfolioManager()

    result = LiveStateStore.restore_into(portfolio, portfolio_manager)

    assert result is None
    assert portfolio.balance == 10000


def test_save_and_load_roundtrip(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    portfolio = Portfolio(10000)

    closed = _open_trade(status="CLOSED")
    closed.profit = 250.0

    portfolio.trades = [closed]
    portfolio.closed_trades = [closed]
    portfolio.balance = 10250.0
    portfolio.balance_history = [10000, 10250.0]

    LiveStateStore.save(portfolio, "2024-01-01 05:00:00")

    saved = LiveStateStore.load()

    assert saved["balance"] == 10250.0
    assert saved["last_processed_timestamp"] == "2024-01-01 05:00:00"
    assert len(saved["trades"]) == 1
    assert saved["trades"][0]["symbol"] == "BTC/USDT"


def test_restore_into_mutates_portfolio_in_place(tmp_path, monkeypatch):
    """
    The core correctness guarantee: restore_into() must not replace
    the Portfolio/PortfolioManager object references, only their
    contents - a Backtester's broker already holds a reference to the
    exact Portfolio object passed to it, so a restore that swapped the
    reference instead of mutating it would leave the broker silently
    writing to a stale, disconnected Portfolio.
    """

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    saved_portfolio = Portfolio(10000)
    open_trade = _open_trade()
    saved_portfolio.trades = [open_trade]
    saved_portfolio.open_positions = [open_trade]
    saved_portfolio.balance = 9500.0

    LiveStateStore.save(saved_portfolio, "2024-01-01 03:00:00")

    portfolio = Portfolio(10000)
    portfolio_manager = PortfolioManager()

    portfolio_id = id(portfolio)
    portfolio_manager_id = id(portfolio_manager)

    timestamp = LiveStateStore.restore_into(portfolio, portfolio_manager)

    assert id(portfolio) == portfolio_id
    assert id(portfolio_manager) == portfolio_manager_id

    assert portfolio.balance == 9500.0
    assert str(timestamp) == "2024-01-01 03:00:00"


def test_restore_into_registers_open_positions_into_portfolio_manager(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    saved_portfolio = Portfolio(10000)
    open_trade = _open_trade(symbol="ETH/USDT")
    closed_trade = _open_trade(symbol="BTC/USDT", status="CLOSED")

    saved_portfolio.trades = [open_trade, closed_trade]
    saved_portfolio.open_positions = [open_trade]
    saved_portfolio.closed_trades = [closed_trade]

    LiveStateStore.save(saved_portfolio, None)

    portfolio = Portfolio(10000)
    portfolio_manager = PortfolioManager()

    LiveStateStore.restore_into(portfolio, portfolio_manager)

    assert portfolio_manager.has_position("ETH/USDT")
    assert not portfolio_manager.has_position("BTC/USDT")

    assert len(portfolio.open_positions) == 1
    assert len(portfolio.closed_trades) == 1


def test_restore_into_reconstructs_trade_side_as_orderside_enum(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    saved_portfolio = Portfolio(10000)
    open_trade = _open_trade()
    saved_portfolio.trades = [open_trade]
    saved_portfolio.open_positions = [open_trade]

    LiveStateStore.save(saved_portfolio, None)

    portfolio = Portfolio(10000)
    portfolio_manager = PortfolioManager()

    LiveStateStore.restore_into(portfolio, portfolio_manager)

    restored_trade = portfolio.trades[0]

    assert restored_trade.side == OrderSide.BUY
    assert isinstance(restored_trade.side, OrderSide)


def test_save_when_no_prior_state_returns_none_on_next_load_call_reflects_last_processed_none(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    portfolio = Portfolio(10000)

    LiveStateStore.save(portfolio, None)

    saved = LiveStateStore.load()

    assert saved["last_processed_timestamp"] is None


def test_save_uses_atomic_write(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")

    calls = {"count": 0}

    original_replace = os.replace

    def counting_replace(src, dst):
        calls["count"] += 1
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", counting_replace)

    portfolio = Portfolio(10000)

    LiveStateStore.save(portfolio, "2024-01-01 00:00:00")

    assert calls["count"] == 1
    assert not (tmp_path / "live_state.tmp").exists()
