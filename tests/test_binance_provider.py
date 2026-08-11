import ccxt
import pandas as pd

from app.data.binance_provider import BinanceProvider

SAMPLE = [
    [1704067200000, 100, 105, 95, 102, 10],
    [1704070800000, 102, 106, 101, 104, 12],
]


def test_fetch_ohlcv_returns_dataframe():

    provider = BinanceProvider()

    provider.exchange.fetch_ohlcv = (
        lambda symbol, timeframe, limit: SAMPLE
    )

    df = provider.fetch_ohlcv("BTC/USDT", "1h", limit=2)

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
    limit in the first place.
    """

    provider = BinanceProvider()

    assert provider.exchange.enableRateLimit is True


def test_fetch_ohlcv_handles_empty_response():

    provider = BinanceProvider()

    provider.exchange.fetch_ohlcv = (
        lambda symbol, timeframe, limit: []
    )

    df = provider.fetch_ohlcv("BTC/USDT", "1h")

    assert df.empty
    assert list(df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]


def test_fetch_ohlcv_handles_rate_limit_error():

    provider = BinanceProvider()

    def raise_rate_limit(symbol, timeframe, limit):
        raise ccxt.RateLimitExceeded("too many requests")

    provider.exchange.fetch_ohlcv = raise_rate_limit

    df = provider.fetch_ohlcv("BTC/USDT", "1h")

    assert df.empty


def test_fetch_ohlcv_handles_network_error():

    provider = BinanceProvider()

    def raise_network_error(symbol, timeframe, limit):
        raise ccxt.NetworkError("connection reset")

    provider.exchange.fetch_ohlcv = raise_network_error

    df = provider.fetch_ohlcv("BTC/USDT", "1h")

    assert df.empty


def test_fetch_ohlcv_handles_exchange_error():

    provider = BinanceProvider()

    def raise_exchange_error(symbol, timeframe, limit):
        raise ccxt.ExchangeError("invalid symbol")

    provider.exchange.fetch_ohlcv = raise_exchange_error

    df = provider.fetch_ohlcv("BTC/USDT", "1h")

    assert df.empty
