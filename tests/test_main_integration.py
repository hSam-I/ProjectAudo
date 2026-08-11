"""
Complements test_end_to_end.py: that file exercises the pipeline
components directly (indicators -> decision -> risk -> backtest).
This file instead calls the actual app.main.main() entry point, so
it also covers what only main() does: exporting reports to disk,
console output, and never touching the network.
"""

import pandas as pd
import pytest

from app.data.binance_provider import BinanceProvider


@pytest.fixture
def fake_binance(random_walk_ohlcv, monkeypatch):

    data = random_walk_ohlcv()

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    return data


def test_main_runs_end_to_end(fake_binance, monkeypatch, tmp_path, capsys):
    """
    Runs app.main.main() through the full production pipeline
    (provider -> validator -> indicators -> features -> decision
    -> risk -> backtest -> reports) with a mocked exchange
    response, and verifies it completes without hitting the
    network and produces the expected reports/console output.
    """

    monkeypatch.chdir(tmp_path)

    from app.main import main

    main()

    output = capsys.readouterr().out

    assert "PROJECT AUDO" in output
    assert "Backtesting" in output
    assert "Performance" in output
    assert "Trade History" in output

    reports_dir = tmp_path / "reports"

    expected_files = [
        "equity_curve.csv",
        "trade_history.csv",
        "equity_curve.png",
        "drawdown.png",
        "trade_distribution.png",
    ]

    for filename in expected_files:

        filepath = reports_dir / filename

        assert filepath.exists(), f"{filename} was not created"
        assert filepath.stat().st_size > 0

    equity_csv = (reports_dir / "equity_curve.csv").read_text()

    assert "Trade" in equity_csv
    assert "Balance" in equity_csv

    trade_csv = (reports_dir / "trade_history.csv").read_text()

    assert "Symbol" in trade_csv
    assert "Entry Time" in trade_csv


def test_main_never_calls_real_exchange(fake_binance, monkeypatch, tmp_path):
    """
    Guards against accidental network access: if fetch_ohlcv is
    ever called without going through the monkeypatched provider,
    this fails instead of the test suite silently hitting Binance.
    """

    monkeypatch.chdir(tmp_path)

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

    from app.main import main

    main()

    assert calls["count"] == 1


def test_main_aborts_on_invalid_market_data(monkeypatch, tmp_path, capsys):
    """
    If the provider returns unusable data (e.g. empty response),
    main() must log the error and return early instead of
    crashing further down the pipeline.
    """

    monkeypatch.chdir(tmp_path)

    def empty_fetch(self, symbol, timeframe, limit=500):
        return pd.DataFrame(
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        )

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        empty_fetch,
    )

    from app.main import main

    main()

    output = capsys.readouterr().out

    assert "PROJECT AUDO" not in output

    assert not (tmp_path / "reports").exists()
