"""
Covers app.execution.live_trader.LiveTrader across both phases of the
live-paper-trading work:

- Phase 1 (settings.enable_live_paper_trading=False, the default):
  OBSERVE ONLY - these tests prove, structurally, that nothing here
  can open a trade (no Backtester is ever constructed).
- Phase 2 (settings.enable_live_paper_trading=True): PAPER TRADING -
  these tests prove Backtester._step() is reused UNCHANGED (same
  signature), filled at a real-time ticker price rather than a
  candle's close, and that state is persisted/restored via
  LiveStateStore.

run_forever() is never called directly (infinite loop) - only
poll_once() is exercised, driven by a fake LiveFeed that returns
synthetic rows without any real polling/sleeping/network access.
"""

from pathlib import Path

import pandas as pd
import pytest

from app.backtesting.portfolio import Portfolio
from app.config.settings import settings
from app.core.enums import Signal
from app.decision.decision_engine import Decision, DecisionEngine
from app.execution.live_state_store import LiveStateStore
from app.execution.live_trader import LiveTrader


@pytest.fixture(autouse=True)
def _isolate_live_state_store(tmp_path, monkeypatch):
    """
    Every paper-trading test in this file goes through
    LiveTrader._ensure_backtester(), which always calls
    LiveStateStore.restore_into()/save() - without this, those calls
    would hit the real data/live_state.json, leaking state between
    test runs (and into the repo itself). Applies to every test here,
    including observe-only ones, since it's harmless when unused.
    """

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")


class FakeProvider:
    """
    Stand-in for BinanceProvider - only fetch_ticker is needed by
    LiveTrader's paper-trading path.
    """

    def __init__(self, ticker_price: float = 100.0):

        self.ticker_price = ticker_price
        self.ticker_calls = []

    def fetch_ticker(self, symbol):

        self.ticker_calls.append(symbol)

        return self.ticker_price


class FakeFeed:
    """
    Drop-in stand-in for LiveFeed: fetch_closed_candles()/select_new_rows()
    are driven directly from a pre-built dataframe and a list of "new"
    rows, with no polling/sleeping/network access at all.
    """

    def __init__(
        self,
        closed: pd.DataFrame,
        new_rows: pd.DataFrame,
        provider: FakeProvider | None = None,
    ):

        self.closed = closed
        self.new_rows = new_rows
        self.processed_timestamps = []
        self.provider = provider or FakeProvider()

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
    Structural guarantee: LiveTrader itself has no attribute that
    could hold a broker/portfolio directly - only a `backtester` slot
    that starts (and, in observe mode, stays) empty.
    """

    closed = _synthetic_df(5)

    trader = LiveTrader(
        "BTC/USDT",
        feed=FakeFeed(closed, closed.iloc[-1:]),
    )

    forbidden_attrs = ("broker", "portfolio", "portfolio_manager")

    for attr in forbidden_attrs:
        assert not hasattr(trader, attr)


def test_observe_mode_never_constructs_a_backtester(monkeypatch):
    """
    With enable_live_paper_trading at its default (False), no
    Backtester is ever built, across any number of polls - the
    structural guarantee that Phase 1's default behavior still cannot
    open a trade, even after Phase 2 added the capability to.
    """

    monkeypatch.setattr(settings, "enable_live_paper_trading", False)

    _force_decision(monkeypatch, signal=Signal.BUY)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    trader.poll_once()
    trader.poll_once()

    assert trader.backtester is None


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


def test_paper_trading_mode_constructs_and_reuses_the_same_backtester(monkeypatch):

    monkeypatch.setattr(settings, "enable_live_paper_trading", True)

    _force_decision(monkeypatch, signal=Signal.HOLD)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    assert trader.backtester is None

    trader.poll_once()

    first_backtester = trader.backtester

    assert first_backtester is not None

    trader.poll_once()

    assert trader.backtester is first_backtester


def test_paper_trading_opens_a_trade_via_step_reuse(monkeypatch):

    monkeypatch.setattr(settings, "enable_live_paper_trading", True)
    monkeypatch.setattr(settings, "slippage", 0.0)
    monkeypatch.setattr(settings, "commission", 0.0)

    _force_decision(monkeypatch, signal=Signal.BUY)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(
        closed,
        closed.iloc[-1:],
        provider=FakeProvider(ticker_price=999.0),
    )

    trader = LiveTrader("BTC/USDT", feed=feed)

    trader.poll_once()

    trades = trader.backtester.portfolio.trades

    assert len(trades) == 1
    assert trades[0].symbol == "BTC/USDT"


def test_paper_trading_fills_at_ticker_price_not_candle_close(monkeypatch):
    """
    The plan's core Faz 2 decision: entry price must come from
    fetch_ticker (a real-time price), not the just-closed candle's
    close - using a stale close would defeat the whole point of this
    turn (measuring the gap between backtest idealization and live
    conditions).
    """

    monkeypatch.setattr(settings, "enable_live_paper_trading", True)
    monkeypatch.setattr(settings, "slippage", 0.0)
    monkeypatch.setattr(settings, "commission", 0.0)

    _force_decision(monkeypatch, signal=Signal.BUY)

    closed = _synthetic_df(settings.warmup_candles + 5)

    candle_close = closed["close"].iloc[-1]

    ticker_price = candle_close + 500.0

    feed = FakeFeed(
        closed,
        closed.iloc[-1:],
        provider=FakeProvider(ticker_price=ticker_price),
    )

    trader = LiveTrader("BTC/USDT", feed=feed)

    trader.poll_once()

    opened_trade = trader.backtester.portfolio.trades[0]

    assert opened_trade.entry_price == ticker_price
    assert opened_trade.entry_price != candle_close
    assert feed.provider.ticker_calls == ["BTC/USDT"]


def test_paper_trading_saves_state_after_each_processed_candle(monkeypatch):

    monkeypatch.setattr(settings, "enable_live_paper_trading", True)

    _force_decision(monkeypatch, signal=Signal.HOLD)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    saved = []

    def fake_save(portfolio, last_processed_timestamp):
        saved.append((portfolio, last_processed_timestamp))

    monkeypatch.setattr(LiveStateStore, "save", staticmethod(fake_save))

    trader.poll_once()

    assert len(saved) == 1
    assert saved[0][0] is trader.backtester.portfolio
    assert saved[0][1] == closed["timestamp"].iloc[-1]


def test_paper_trading_restores_state_on_first_step(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveStateStore, "FILE", tmp_path / "live_state.json")
    monkeypatch.setattr(settings, "enable_live_paper_trading", True)

    prior_portfolio = Portfolio(10000)
    prior_portfolio.balance = 12345.0
    prior_portfolio.balance_history = [10000, 12345.0]

    LiveStateStore.save(prior_portfolio, "2023-12-31 23:00:00")

    _force_decision(monkeypatch, signal=Signal.HOLD)

    closed = _synthetic_df(settings.warmup_candles + 5)

    feed = FakeFeed(closed, closed.iloc[-1:])

    trader = LiveTrader("BTC/USDT", feed=feed)

    trader.poll_once()

    assert trader.backtester.portfolio.balance == 12345.0
    assert pd.Timestamp("2023-12-31 23:00:00") in feed.processed_timestamps


def test_live_execution_modules_never_reference_real_order_placement():
    """
    Automated guarantee from the plan's Soru 6, expanded per feedback
    on Faz 1: this scans the app/execution/ directory dynamically
    (glob on "live_*.py", never a hardcoded filename list) so any
    live_*.py file added in a future phase - live_state_store.py
    today, whatever comes in Faz 3 - is automatically covered without
    remembering to update this test. Neither live_feed.py,
    live_trader.py, nor live_state_store.py's source may reference a
    real order-placement ccxt call or API credentials - the live
    trading path (now including real paper position-taking as of
    Faz 2) must remain structurally incapable of sending a real order.
    """

    forbidden = (
        "create_order",
        "create_market_order",
        "create_limit_order",
        "apiKey",
        "secret",
    )

    execution_dir = Path(__file__).resolve().parent.parent / "app" / "execution"

    scanned_files = list(execution_dir.glob("live_*.py"))

    # Guards against the glob silently matching nothing (e.g. a typo'd
    # pattern) and this test passing vacuously.
    assert len(scanned_files) >= 3

    for path in scanned_files:

        source = path.read_text(encoding="utf-8")

        for keyword in forbidden:
            assert keyword not in source, f"{keyword!r} found in {path.name}"
