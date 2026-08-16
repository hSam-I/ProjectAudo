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
from app.data.validator import DataValidator
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


# --- Timestamp-gap handling (feature/multi-symbol-gap-handling) ---
#
# Each symbol individually passes DataValidator (>= MINIMUM_ROWS=60 rows,
# no internal gap), but _align_timestamps' set-intersection can still
# produce an empty, too-short, or internally-gapped shared axis. See
# CLAUDE.md "Bilinen sorunlar" madde 5 for why this is a narrower and
# differently-shaped problem than originally documented, and
# Backtester._run_multi's docstring-less inline comments for why a
# gapped shared axis stops the whole run instead of dropping a symbol
# (unlike the per-symbol invalid-data skip covered by the tests above).


def _custom_ohlcv(timestamps, seed=0):
    """
    Builds a valid OHLCV frame at explicit timestamps - for phase/gap/
    timeframe scenarios that conftest's random_walk_ohlcv (fixed hourly
    grid from a fixed 2024-01-01 start) can't express.
    """

    import numpy as np
    import pandas as pd

    ordered = sorted(timestamps)

    rng = np.random.default_rng(seed)
    close = 200 + np.cumsum(rng.normal(0, 1, len(ordered)))

    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(ordered),
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": [1000.0] * len(ordered),
        }
    )


def test_run_multi_warns_and_stops_on_empty_intersection(monkeypatch, caplog):

    import pandas as pd

    monkeypatch.setattr(settings, "enable_multi_position", True)

    a = _custom_ohlcv(pd.date_range("2026-01-01 00:00", periods=100, freq="1h"), seed=1)
    b = _custom_ohlcv(pd.date_range("2026-01-01 00:30", periods=100, freq="1h"), seed=2)

    backtester = Backtester()

    with caplog.at_level(logging.WARNING):
        portfolio = backtester.run({"A": a, "B": b})

    assert portfolio is backtester.portfolio
    assert portfolio.total_trades == 0

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any(
        "no common timestamps" in w and "did not run" in w
        for w in warnings
    )


def test_run_multi_warns_and_stops_on_too_short_intersection(monkeypatch, caplog):

    import pandas as pd

    monkeypatch.setattr(settings, "enable_multi_position", True)

    a = _custom_ohlcv(pd.date_range("2026-01-01 00:00", periods=100, freq="1h"), seed=1)
    # Overlaps A on only the last ~24 hours - well under warmup_candles+2.
    b = _custom_ohlcv(pd.date_range("2026-01-04 04:00", periods=100, freq="1h"), seed=2)

    backtester = Backtester()

    with caplog.at_level(logging.WARNING):
        portfolio = backtester.run({"A": a, "B": b})

    assert portfolio is backtester.portfolio
    assert portfolio.total_trades == 0

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any(
        "zero backtest steps" in w and "warmup_candles" in w
        for w in warnings
    )


def test_run_multi_warns_but_runs_on_intersection_below_minimum_rows(monkeypatch, caplog):
    """
    Intersection length lands strictly between warmup_candles+2 (the
    minimum for the candle loop to execute at least once) and
    DataValidator.MINIMUM_ROWS (60, the per-symbol validation floor) -
    each symbol individually clears MINIMUM_ROWS, but their overlap
    doesn't. This should warn (statistically thin) without stopping.
    """

    import pandas as pd

    monkeypatch.setattr(settings, "enable_multi_position", True)

    _force_buy(monkeypatch)

    a = _custom_ohlcv(pd.date_range("2026-01-01 00:00", periods=70, freq="1h"), seed=1)
    b = _custom_ohlcv(pd.date_range("2026-01-01 15:00", periods=70, freq="1h"), seed=2)
    # Overlap: 2026-01-01 15:00 .. 2026-01-03 21:00 -> 55 candles.

    backtester = Backtester()

    with caplog.at_level(logging.WARNING):
        portfolio = backtester.run({"A": a, "B": b})

    assert len(portfolio.trades) > 0

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any(
        "MINIMUM_ROWS" in w and "55" in w
        for w in warnings
    )


def test_run_multi_raises_on_mixed_timeframes(monkeypatch):

    import pandas as pd

    monkeypatch.setattr(settings, "enable_multi_position", True)

    hourly = _custom_ohlcv(pd.date_range("2026-01-01", periods=300, freq="1h"), seed=1)
    two_hourly = _custom_ohlcv(pd.date_range("2026-01-01", periods=150, freq="2h"), seed=2)

    with pytest.raises(ValueError, match="different candle timeframes"):
        Backtester().run({"HOURLY": hourly, "TWO_HOURLY": two_hourly})


def test_run_multi_raises_on_gap_in_aligned_axis(monkeypatch):
    """
    Constructs two symbols that each individually pass DataValidator
    (including its own evenly-spaced check) but whose raw timestamp
    sets diverge at two different points. The intersection therefore
    drops both points, reintroducing two single-candle gaps that DO
    fail the evenly-spaced check - a gap that exists only on the
    shared aligned axis, not on either symbol's own raw data. See
    Backtester._describe_alignment_gap's docstring for why this raises
    (naming both offending symbols) instead of dropping one of them.
    """

    import pandas as pd

    monkeypatch.setattr(settings, "enable_multi_position", True)

    grid = list(pd.date_range("2026-01-01", periods=90, freq="2h"))

    g_ts = list(grid)
    g_ts[40] = g_ts[40] - pd.Timedelta(hours=1)

    h_ts = list(grid)
    h_ts[50] = h_ts[50] - pd.Timedelta(hours=1)

    g = _custom_ohlcv(g_ts, seed=1)
    h = _custom_ohlcv(h_ts, seed=2)

    assert DataValidator.validate(g)
    assert DataValidator.validate(h)

    with pytest.raises(ValueError) as excinfo:
        Backtester().run({"G": g, "H": h})

    message = str(excinfo.value)

    assert "G" in message
    assert "H" in message


def test_run_multi_clean_overlap_produces_no_new_alignment_warnings(random_walk_ohlcv, monkeypatch, caplog):
    """
    Regression guard: two symbols with an identical, fully-overlapping
    hourly grid should trip none of the new gap/empty/short-intersection
    warnings - only the pre-existing per-symbol invalid-data warning
    path (unused here) can fire.
    """

    monkeypatch.setattr(settings, "enable_multi_position", True)

    _force_buy(monkeypatch)

    df = random_walk_ohlcv(seed=1)

    with caplog.at_level(logging.WARNING):
        portfolio = Backtester().run({"SYM_A": df.copy(), "SYM_B": df.copy()})

    assert len(portfolio.trades) > 0
    assert caplog.records == []
