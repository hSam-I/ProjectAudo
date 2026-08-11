"""
Covers Phase 1 of the live-paper-trading work (branch
feature/live-paper-trading): app.execution.live_feed.LiveFeed, the
polling/candle-detection layer. No test calls wait_for_next_candle()
or run_forever() (both sleep/loop indefinitely) - only the pure
timing-math and row-selection logic is exercised here.
"""

import logging

import pandas as pd
import pytest

from app.data.binance_provider import BinanceProvider
from app.execution.live_feed import LiveFeed, timeframe_to_seconds


def test_timeframe_to_seconds():

    assert timeframe_to_seconds("1m") == 60
    assert timeframe_to_seconds("15m") == 900
    assert timeframe_to_seconds("1h") == 3600
    assert timeframe_to_seconds("4h") == 14400
    assert timeframe_to_seconds("1d") == 86400
    assert timeframe_to_seconds("1w") == 604800


def test_timeframe_to_seconds_rejects_unsupported_unit():

    with pytest.raises(ValueError):
        timeframe_to_seconds("1M")


def test_seconds_until_next_close_for_hourly_timeframe():

    feed = LiveFeed("BTC/USDT", timeframe="1h", provider=object())

    now = pd.Timestamp("2024-01-01 12:34:56")

    assert feed.seconds_until_next_close(now) == 3600 - (34 * 60 + 56)


def test_seconds_until_next_close_for_15m_timeframe():

    feed = LiveFeed("BTC/USDT", timeframe="15m", provider=object())

    now = pd.Timestamp("2024-01-01 12:34:56")

    assert feed.seconds_until_next_close(now) == 900 - (4 * 60 + 56)


def test_seconds_until_next_close_is_within_one_interval():

    feed = LiveFeed("BTC/USDT", timeframe="1h", provider=object())

    for minute in (0, 1, 30, 59):

        now = pd.Timestamp(f"2024-06-15 08:{minute:02d}:00")

        result = feed.seconds_until_next_close(now)

        assert 0 < result <= feed.interval_seconds


def _synthetic_df(n: int, seed: int = 0) -> pd.DataFrame:

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


def test_fetch_closed_candles_drops_the_last_row(monkeypatch):

    data = _synthetic_df(10)

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(BinanceProvider, "fetch_ohlcv", fake_fetch_ohlcv)

    feed = LiveFeed("BTC/USDT")

    closed = feed.fetch_closed_candles()

    assert len(closed) == 9
    assert closed["timestamp"].iloc[-1] == data["timestamp"].iloc[-2]


def test_select_new_rows_first_poll_returns_only_latest_candle():

    feed = LiveFeed("BTC/USDT", provider=object())

    closed = _synthetic_df(5)

    new_rows = feed.select_new_rows(closed)

    assert len(new_rows) == 1
    assert new_rows["timestamp"].iloc[0] == closed["timestamp"].iloc[-1]


def test_select_new_rows_returns_rows_after_last_processed():

    feed = LiveFeed("BTC/USDT", provider=object())

    closed = _synthetic_df(5)

    feed.mark_processed(closed["timestamp"].iloc[2])

    new_rows = feed.select_new_rows(closed)

    assert list(new_rows["timestamp"]) == list(closed["timestamp"].iloc[3:])


def test_select_new_rows_logs_warning_on_missed_candles(caplog):

    feed = LiveFeed("BTC/USDT", provider=object())

    closed = _synthetic_df(5)

    feed.mark_processed(closed["timestamp"].iloc[0])

    with caplog.at_level(logging.WARNING):
        new_rows = feed.select_new_rows(closed)

    assert len(new_rows) == 4

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert any("3 candle(s) missed" in w for w in warnings)


def test_select_new_rows_no_warning_for_single_new_candle(caplog):

    feed = LiveFeed("BTC/USDT", provider=object())

    closed = _synthetic_df(5)

    feed.mark_processed(closed["timestamp"].iloc[3])

    with caplog.at_level(logging.WARNING):
        new_rows = feed.select_new_rows(closed)

    assert len(new_rows) == 1

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert not warnings


def test_mark_processed_updates_state():

    feed = LiveFeed("BTC/USDT", provider=object())

    assert feed.last_processed_timestamp is None

    timestamp = pd.Timestamp("2024-01-01 05:00:00")

    feed.mark_processed(timestamp)

    assert feed.last_processed_timestamp == timestamp
