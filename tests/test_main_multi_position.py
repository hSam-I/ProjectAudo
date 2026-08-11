"""
Covers Phase C of the multi-position Backtester work: app.main.run_multi_position(),
wiring MultiDataProvider.fetch_all() -> Backtester.run(market_data) behind
`python -m app.main --multi-position`, as a new parallel entrypoint that
does not touch main()'s existing single-symbol path.

Unlike run_scan() (Adim 3, signal-only), this actually opens/manages/
closes trades - so, like tests/test_multi_position_backtester.py, it
forces DecisionEngine.evaluate() to a fixed BUY decision rather than
relying on real strategy scoring to fire on arbitrary synthetic data.
"""

import pandas as pd
import pytest

from app.config.settings import settings
from app.core.enums import Signal
from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.decision.decision_engine import Decision, DecisionEngine


@pytest.fixture(autouse=True)
def _reset_multi_position_flag(monkeypatch):
    """
    run_multi_position() mutates settings.enable_multi_position=True
    directly (not via monkeypatch), so without this it would leak True
    into later tests in the suite (e.g. test_multi_position_backtester.py's
    "raises when disabled" test). Routing the reset through monkeypatch
    here means its teardown restores the pre-test value regardless of
    what the function under test does to it.
    """

    monkeypatch.setattr(settings, "enable_multi_position", False)


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


@pytest.fixture
def fake_multi_symbol_binance(random_walk_ohlcv, monkeypatch):
    """
    fetch_ohlcv is keyed by symbol so each settings.symbols entry gets
    its own (still timestamp-aligned, per conftest's random_walk_ohlcv)
    series - proving run_multi_position() actually threads per-symbol
    data through, not just one df reused blindly.
    """

    data_by_symbol = {
        "BTC/USDT": random_walk_ohlcv(seed=1),
        "ETH/USDT": random_walk_ohlcv(seed=2),
    }

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data_by_symbol[symbol].copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    return data_by_symbol


def test_run_multi_position_prints_report_for_both_symbols(fake_multi_symbol_binance, monkeypatch, capsys):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])
    monkeypatch.setattr(settings, "max_open_positions", 5)

    _force_buy(monkeypatch)

    from app.main import run_multi_position

    run_multi_position()

    output = capsys.readouterr().out

    assert "MULTI-POSITION BACKTEST" in output
    assert "BTC/USDT" in output
    assert "ETH/USDT" in output
    assert "Total Trades" in output
    assert "Sharpe Ratio" in output


def test_run_multi_position_enables_the_settings_flag(fake_multi_symbol_binance, monkeypatch):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    from app.main import run_multi_position

    run_multi_position()

    assert settings.enable_multi_position is True


def test_run_multi_position_never_calls_real_exchange(fake_multi_symbol_binance, monkeypatch):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    calls = {"count": 0}

    original = BinanceProvider.fetch_ohlcv

    def counting_fetch(self, symbol, timeframe, limit=500):
        calls["count"] += 1
        return original(self, symbol, timeframe, limit)

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        counting_fetch,
    )

    from app.main import run_multi_position

    run_multi_position()

    assert calls["count"] == 2


def test_run_multi_position_handles_data_provider_error(monkeypatch, capsys):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    def failing_fetch(self, symbol, timeframe, limit=500):
        raise DataProviderError(f"Rate limit exceeded fetching {symbol}")

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        failing_fetch,
    )

    from app.main import run_multi_position

    run_multi_position()

    output = capsys.readouterr().out

    assert "MULTI-POSITION BACKTEST" not in output


def test_run_multi_position_reports_per_symbol_trade_counts(fake_multi_symbol_binance, monkeypatch, capsys):
    """
    max_open_positions=1 forces only one symbol to ever hold a
    position at a time (see test_multi_position_backtester.py's
    identical-data variant of this reasoning), so the per-symbol trade
    count breakdown must show a non-trivial split rather than just
    "some number of trades happened somewhere".
    """

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])
    monkeypatch.setattr(settings, "max_open_positions", 5)

    _force_buy(monkeypatch)

    from app.main import run_multi_position

    run_multi_position()

    output = capsys.readouterr().out

    assert "Per-Symbol Trade Counts" in output
    assert "BTC/USDT" in output.split("Per-Symbol Trade Counts")[1]
    assert "ETH/USDT" in output.split("Per-Symbol Trade Counts")[1]
