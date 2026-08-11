"""
Covers Phase B of the multi-position Backtester work (branch
feature/multi-position-backtester): Backtester.run() accepting a
dict[symbol, DataFrame] to run a real multi-symbol backtest sharing one
Portfolio's balance/risk limits, gated behind settings.enable_multi_position
(default False - a safety rail, not a capability check).

Decisions are forced to BUY via a monkeypatched DecisionEngine.evaluate()
in most tests here, rather than relying on real strategy signals: the
default ema_rsi strategy's raw BUY only survives SignalFilter if the
combined score clears BUY_THRESHOLD=60, which depends on feature/market
data this suite doesn't try to engineer - these tests are about the
Backtester's multi-symbol mechanics (position gating, shared risk caps,
timestamp alignment, per-symbol validation skip), not strategy scoring.
"""

import logging

import pytest

from app.backtesting.backtester import Backtester
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.decision_engine import Decision, DecisionEngine


def _force_buy(monkeypatch):

    def fake_evaluate(self, df):

        return Decision(
            raw_signal=Signal.BUY,
            signal=Signal.BUY,
            score=100,
            confidence="high",
            reasons=[],
            regime="UNKNOWN",
        )

    monkeypatch.setattr(DecisionEngine, "evaluate", fake_evaluate)


def _max_concurrent_open(trades) -> int:
    """
    Reconstructs peak simultaneous open-position count from closed
    trades' [entry_time, exit_time) intervals. Closes are ordered
    before opens at an identical timestamp, since Backtester._step()
    always closes a symbol's expiring position before any other
    symbol's open check runs on that same candle - a same-candle
    handoff must not count as 2 concurrent positions.
    """

    import pandas as pd

    events = []

    for trade in trades:

        if trade.exit_time is None:
            continue

        events.append((pd.to_datetime(trade.entry_time), 1))
        events.append((pd.to_datetime(trade.exit_time), -1))

    events.sort(key=lambda event: (event[0], event[1]))

    running = 0
    peak = 0

    for _, delta in events:
        running += delta
        peak = max(peak, running)

    return peak


def test_run_raises_when_multi_position_disabled(random_walk_ohlcv):

    market_data = {
        "SYM_A": random_walk_ohlcv(seed=1),
        "SYM_B": random_walk_ohlcv(seed=2),
    }

    with pytest.raises(ValueError):
        Backtester().run(market_data)


def test_run_multi_allows_concurrent_positions_across_symbols(random_walk_ohlcv, monkeypatch):

    monkeypatch.setattr(settings, "enable_multi_position", True)
    monkeypatch.setattr(settings, "max_open_positions", 5)

    _force_buy(monkeypatch)

    market_data = {
        "SYM_A": random_walk_ohlcv(seed=1),
        "SYM_B": random_walk_ohlcv(seed=2),
    }

    portfolio = Backtester().run(market_data)

    traded_symbols = {trade.symbol for trade in portfolio.trades}

    assert traded_symbols == {"SYM_A", "SYM_B"}
    assert _max_concurrent_open(portfolio.closed_trades) >= 2


def test_max_open_positions_caps_total_across_symbols(random_walk_ohlcv, monkeypatch):
    """
    Both symbols see identical price data and an identical forced-BUY
    decision at every candle, so with max_open_positions=1 the shared
    PortfolioRiskManager.can_open_position() check must never let a
    second position open while one is already open - regardless of
    which symbol currently holds it.
    """

    monkeypatch.setattr(settings, "enable_multi_position", True)
    monkeypatch.setattr(settings, "max_open_positions", 1)

    _force_buy(monkeypatch)

    df = random_walk_ohlcv()

    market_data = {"SYM_A": df.copy(), "SYM_B": df.copy()}

    portfolio = Backtester().run(market_data)

    assert len(portfolio.trades) > 0
    assert _max_concurrent_open(portfolio.closed_trades) <= 1


def test_align_timestamps_logs_dropped_candles_per_symbol(random_walk_ohlcv, caplog):

    long_df = random_walk_ohlcv(n=500, seed=1)
    short_df = random_walk_ohlcv(n=450, seed=2)

    with caplog.at_level(logging.WARNING):

        aligned = Backtester._align_timestamps(
            {
                "LONG": long_df,
                "SHORT": short_df,
            }
        )

    assert len(aligned["LONG"]) == 450
    assert len(aligned["SHORT"]) == 450

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any("LONG" in w and "50" in w for w in warnings)
    assert not any("SHORT" in w for w in warnings)


def test_run_multi_skips_invalid_symbol_and_continues_with_others(random_walk_ohlcv, monkeypatch, caplog):

    monkeypatch.setattr(settings, "enable_multi_position", True)

    _force_buy(monkeypatch)

    market_data = {
        "VALID_A": random_walk_ohlcv(seed=1),
        "INVALID": random_walk_ohlcv(n=30),
        "VALID_B": random_walk_ohlcv(seed=2),
    }

    with caplog.at_level(logging.WARNING):
        portfolio = Backtester().run(market_data)

    traded_symbols = {trade.symbol for trade in portfolio.trades}

    assert traded_symbols == {"VALID_A", "VALID_B"}
    assert "INVALID" not in traded_symbols

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any("INVALID" in w for w in warnings)


def test_run_multi_returns_unchanged_portfolio_when_no_valid_symbols(random_walk_ohlcv, monkeypatch, caplog):

    monkeypatch.setattr(settings, "enable_multi_position", True)

    market_data = {
        "INVALID_A": random_walk_ohlcv(n=30),
        "INVALID_B": random_walk_ohlcv(n=10),
    }

    backtester = Backtester()

    with caplog.at_level(logging.WARNING):
        portfolio = backtester.run(market_data)

    assert portfolio is backtester.portfolio
    assert portfolio.total_trades == 0
