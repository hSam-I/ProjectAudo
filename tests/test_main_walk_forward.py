"""
Covers app.main.run_walk_forward() (Step 2 of the orphan-module
integration): productionizes the WalkForwardAnalyzer pattern already
proven out in tests/test_ema_rsi_walk_forward.py, wiring it behind
`python -m app.main --walk-forward` instead of only existing as a
test-only helper.
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


def test_run_walk_forward_prints_report_for_each_window(fake_binance, monkeypatch, tmp_path, capsys):

    monkeypatch.chdir(tmp_path)

    from app.main import run_walk_forward

    run_walk_forward()

    output = capsys.readouterr().out

    assert "WALK-FORWARD REPORT" in output
    # candle_limit=500, train=250/test=100 defaults -> 2 windows.
    assert "Window 0" in output
    assert "Window 1" in output
    assert "Train:" in output
    assert "Test :" in output


def test_run_walk_forward_never_calls_real_exchange(fake_binance, monkeypatch, tmp_path):

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

    from app.main import run_walk_forward

    run_walk_forward()

    assert calls["count"] == 1


def test_run_walk_forward_warns_on_insufficient_data(random_walk_ohlcv, monkeypatch, tmp_path, capsys):
    """
    train_size(250) + test_size(100) = 350 candles needed for a single
    window; 200 valid candles is enough to pass DataValidator but not
    enough to produce a window, and must not crash.
    """

    monkeypatch.chdir(tmp_path)

    data = random_walk_ohlcv(n=200)

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    from app.main import run_walk_forward

    run_walk_forward()

    output = capsys.readouterr().out

    assert "WALK-FORWARD REPORT" not in output


def test_run_walk_forward_aborts_on_invalid_market_data(monkeypatch, tmp_path, capsys):

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

    from app.main import run_walk_forward

    run_walk_forward()

    output = capsys.readouterr().out

    assert "WALK-FORWARD REPORT" not in output
