"""
Covers app.main.run_scan() (Step 3 of the orphan-module integration):
wires app.scheduler.Scheduler -> MultiAssetBacktester -> MultiDataProvider
-> MarketScanner -> DecisionEngine.evaluate behind `python -m app.main
--scan`, as a new parallel entrypoint that does not touch main()'s
existing single-symbol backtest path.

Confirms the open question from the integration plan: MultiDataProvider
calls BinanceProvider.fetch_ohlcv() internally (app/data/multi_data_provider.py),
so it already inherits BinanceProvider's ccxt-error -> DataProviderError
wrapping - no separate error handling was needed inside MultiDataProvider
itself, only a try/except at the run_scan() call site (same pattern as
main()'s own fetch).
"""

from app.config.settings import settings
from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError


def test_run_scan_prints_decision_per_symbol(random_walk_ohlcv, monkeypatch, capsys):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    data = random_walk_ohlcv()

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    from app.main import run_scan

    run_scan()

    output = capsys.readouterr().out

    assert "MARKET SCAN" in output
    assert "BTC/USDT" in output
    assert "ETH/USDT" in output
    assert "signal=" in output
    assert "regime=" in output


def test_run_scan_never_calls_real_exchange(random_walk_ohlcv, monkeypatch):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT", "ETH/USDT"])

    data = random_walk_ohlcv()

    calls = {"count": 0}

    def counting_fetch(self, symbol, timeframe, limit=500):
        calls["count"] += 1
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        counting_fetch,
    )

    from app.main import run_scan

    run_scan()

    assert calls["count"] == 2


def test_run_scan_handles_data_provider_error(monkeypatch, capsys):

    monkeypatch.setattr(settings, "symbols", ["BTC/USDT"])

    def failing_fetch(self, symbol, timeframe, limit=500):
        raise DataProviderError(f"Rate limit exceeded fetching {symbol}")

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        failing_fetch,
    )

    from app.main import run_scan

    run_scan()

    output = capsys.readouterr().out

    assert "MARKET SCAN" not in output
