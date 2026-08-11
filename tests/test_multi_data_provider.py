"""
Resolves the open question from the Step 3 integration plan: does
MultiDataProvider.fetch_all() inherit BinanceProvider's ccxt-error ->
DataProviderError wrapping, or does it need its own try/except?

MultiDataProvider.fetch_all() (app/data/multi_data_provider.py) calls
self.provider.fetch_ohlcv() where self.provider is a BinanceProvider,
so any ccxt.RateLimitExceeded/NetworkError/ExchangeError already
becomes a DataProviderError before it reaches MultiDataProvider - no
separate error handling was needed there.
"""

import pytest

from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.data.multi_data_provider import MultiDataProvider


def test_fetch_all_returns_data_per_symbol(random_walk_ohlcv, monkeypatch):

    data = random_walk_ohlcv()

    def fake_fetch_ohlcv(self, symbol, timeframe, limit=500):
        return data.copy()

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        fake_fetch_ohlcv,
    )

    result = MultiDataProvider().fetch_all(
        symbols=["BTC/USDT", "ETH/USDT"],
        timeframe="1h",
    )

    assert set(result.keys()) == {"BTC/USDT", "ETH/USDT"}
    assert len(result["BTC/USDT"]) == len(data)


def test_fetch_all_propagates_data_provider_error(monkeypatch):

    def failing_fetch(self, symbol, timeframe, limit=500):
        raise DataProviderError(f"Exchange error fetching {symbol}")

    monkeypatch.setattr(
        BinanceProvider,
        "fetch_ohlcv",
        failing_fetch,
    )

    with pytest.raises(DataProviderError):

        MultiDataProvider().fetch_all(
            symbols=["BTC/USDT"],
            timeframe="1h",
        )
