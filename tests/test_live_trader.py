"""
Covers Phase 1 of the live-paper-trading work: app.execution.live_trader.LiveTrader.
OBSERVE ONLY - these tests exist specifically to prove, structurally,
that nothing here can open a trade (no Backtester/PaperBroker/Portfolio
is ever constructed), matching the plan's Soru 6 safety requirement.

run_forever() is never called directly (infinite loop) - only
poll_once() is exercised, driven by a fake LiveFeed that returns
synthetic rows without any real polling/sleeping.
"""

from pathlib import Path

import pandas as pd

from app.config.settings import settings
from app.core.enums import Signal
from app.decision.decision_engine import Decision, DecisionEngine
from app.execution.live_trader import LiveTrader


class FakeFeed:
    """
    Drop-in stand-in for LiveFeed: fetch_closed_candles()/select_new_rows()
    are driven directly from a pre-built dataframe and a list of "new"
    rows, with no polling/sleeping/network access at all.
    """

    def __init__(self, closed: pd.DataFrame, new_rows: pd.DataFrame):

        self.closed = closed
        self.new_rows = new_rows
        self.processed_timestamps = []

    def fetch_closed_candles(self):
        return self.closed

    def select_new_rows(self, closed):
        return self.new_rows

    def mark_processed(self, timestamp):
        self.processed_timestamps.append(timestamp)


def _synthetic_df(n: int) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="1h"),
            "open": [100.0 + i for i in range(n)],
            "high": [101.0 + i for i in range(n)],
            "low": [99.0 + i for i in range(n)],
            "close": [100.5 + i for i in range(n)],
            "volume": [1000.0] * n,
        }
    )


def _force_decision(monkeypatch, signal=Signal.HOLD):

    def fake_evaluate(self, df):

        return Decision(
            raw_signal=signal,
            signal=signal,
            score=50,
            confidence="medium",
            reasons=[],
            regime="UNKNOWN",
        )

    monkeypatch.setattr(DecisionEngine, "evaluate", fake_evaluate)

    return fake_evaluate


def test_live_trader_never_constructs_a_broker_or_portfolio():
    """
    Structural guarantee: LiveTrader has no attribute that could hold a
    broker/portfolio - Phase 1 cannot open a trade because there is
    nothing here capable of executing one.
    """

    closed = _synthetic_df(5)

    trader = LiveTrader(
        "BTC/USDT",
        feed=FakeFeed(closed, closed.iloc[-1:]),
    )

    forbidden_attrs = ("broker", "portfolio", "portfolio_manager")

    for attr in forbidden_attrs:
        assert not hasattr(trader, attr)


def test_poll_once_skips_evaluation_during_warmup(monkeypatch):

    fake_evaluate = _force_decision(monkeypatch)

    closed = _synthetic_df(settings.warmup_candles - 1)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    calls = {"count": 0}

    original = DecisionEngine.evaluate

    def counting_evaluate(self, df):
        calls["count"] += 1
        return original(self, df)

    monkeypatch.setattr(DecisionEngine, "evaluate", counting_evaluate)

    trader.poll_once()

    assert calls["count"] == 0
    assert len(feed.processed_timestamps) == 1


def test_poll_once_evaluates_and_logs_after_warmup(monkeypatch, caplog):

    import logging

    _force_decision(monkeypatch, signal=Signal.BUY)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    with caplog.at_level(logging.INFO):
        trader.poll_once()

    assert len(feed.processed_timestamps) == 1

    messages = [record.message for record in caplog.records]

    assert any("OBSERVE ONLY" in m and "BUY" in m for m in messages)


def test_poll_once_processes_multiple_new_candles_in_order(monkeypatch):

    calls = []

    def fake_evaluate(self, df):

        calls.append(df["timestamp"].iloc[-1])

        return Decision(
            raw_signal=Signal.HOLD,
            signal=Signal.HOLD,
            score=0,
            confidence="low",
            reasons=[],
            regime="UNKNOWN",
        )

    monkeypatch.setattr(DecisionEngine, "evaluate", fake_evaluate)

    n = settings.warmup_candles + 3

    closed = _synthetic_df(n)

    new_rows = closed.iloc[-3:]

    feed = FakeFeed(closed, new_rows)

    trader = LiveTrader("BTC/USDT", feed=feed)

    trader.poll_once()

    assert calls == list(new_rows["timestamp"])
    assert feed.processed_timestamps == list(new_rows["timestamp"])


def test_live_execution_modules_never_reference_real_order_placement():
    """
    Automated guarantee from the plan's Soru 6: neither live_feed.py nor
    live_trader.py's source may reference a real order-placement ccxt
    call or API credentials - Phase 1 (and beyond) must remain
    structurally incapable of sending a real order.
    """

    forbidden = (
        "create_order",
        "create_market_order",
        "create_limit_order",
        "apiKey",
        "secret",
    )

    execution_dir = Path(__file__).resolve().parent.parent / "app" / "execution"

    for path in execution_dir.glob("live_*.py"):

        source = path.read_text(encoding="utf-8")

        for keyword in forbidden:
            assert keyword not in source, f"{keyword!r} found in {path.name}"
