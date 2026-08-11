import ccxt
import pandas as pd
import pytest

from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError


def test_fetch_ohlcv_returns_dataframe(monkeypatch):

    provider = BinanceProvider()

    raw = [
        [1704067200000, 100.0, 101.0, 99.0, 100.5, 1000.0],
        [1704070800000, 100.5, 102.0, 100.0, 101.5, 1200.0],
    ]

    monkeypatch.setattr(
        provider.exchange,
        "fetch_ohlcv",
        lambda *args, **kwargs: raw,
    )

    df = provider.fetch_ohlcv(
        symbol="BTC/USDT",
        timeframe="1h",
        limit=2,
    )

    assert list(df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert len(df) == 2
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])


def test_provider_enables_rate_limiting():
    """
    ccxt's built-in throttling avoids tripping Binance's rate
    limit in the first place, on top of catching it when it
    still happens.
    """

    provider = BinanceProvider()

    assert provider.exchange.enableRateLimit is True


@pytest.mark.parametrize(
    "raised",
    [
        ccxt.RateLimitExceeded("binance rate limit exceeded"),
        ccxt.RequestTimeout("request timed out"),
        ccxt.ExchangeNotAvailable("exchange under maintenance"),
        ccxt.BadSymbol("bad symbol XYZ/ABC"),
        ccxt.ExchangeError("generic exchange error"),
    ],
)
def test_fetch_ohlcv_wraps_ccxt_errors(monkeypatch, raised):

    provider = BinanceProvider()

    def _raise(*args, **kwargs):
        raise raised

    monkeypatch.setattr(
        provider.exchange,
        "fetch_ohlcv",
        _raise,
    )

    with pytest.raises(DataProviderError):

        provider.fetch_ohlcv(
            symbol="BTC/USDT",
            timeframe="1h",
            limit=500,
        )
