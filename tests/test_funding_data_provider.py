import ccxt
import pytest

from app.arbitrage.funding_data_provider import FundingDataProvider
from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError


def test_wraps_a_binance_provider_for_the_spot_leg():

    provider = FundingDataProvider()

    assert isinstance(provider.spot, BinanceProvider)


def test_accepts_an_injected_spot_provider():

    spot = BinanceProvider()

    provider = FundingDataProvider(spot_provider=spot)

    assert provider.spot is spot


def test_futures_exchange_enables_rate_limiting():

    provider = FundingDataProvider()

    assert provider._futures_exchange.enableRateLimit is True


def test_futures_exchange_is_configured_for_the_futures_market():
    """
    ccxt needs options={"defaultType": "future"} to address perpetual
    markets (BTC/USDT:USDT) rather than spot (BTC/USDT) - without this
    every call below would silently hit the wrong market.
    """

    provider = FundingDataProvider()

    assert provider._futures_exchange.options.get("defaultType") == "future"


def test_fetch_funding_rate_history_returns_raw_entries(monkeypatch):

    provider = FundingDataProvider()

    raw = [
        {"timestamp": 1704067200000, "fundingRate": 0.0001},
        {"timestamp": 1704096000000, "fundingRate": -0.00005},
    ]

    monkeypatch.setattr(
        provider._futures_exchange,
        "fetch_funding_rate_history",
        lambda symbol, since=None, limit=1000: raw,
    )

    result = provider.fetch_funding_rate_history("BTC/USDT:USDT")

    assert result == raw


def test_fetch_funding_rate_returns_the_rate_only(monkeypatch):

    provider = FundingDataProvider()

    monkeypatch.setattr(
        provider._futures_exchange,
        "fetch_funding_rate",
        lambda symbol: {"symbol": symbol, "fundingRate": 0.0001234},
    )

    rate = provider.fetch_funding_rate("BTC/USDT:USDT")

    assert rate == 0.0001234


def test_fetch_perp_ticker_returns_last_price(monkeypatch):

    provider = FundingDataProvider()

    monkeypatch.setattr(
        provider._futures_exchange,
        "fetch_ticker",
        lambda symbol: {"symbol": symbol, "last": 64000.5},
    )

    price = provider.fetch_perp_ticker("BTC/USDT:USDT")

    assert price == 64000.5


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
@pytest.mark.parametrize(
    "method_name, call",
    [
        (
            "fetch_funding_rate_history",
            lambda p: p.fetch_funding_rate_history("BTC/USDT:USDT"),
        ),
        (
            "fetch_funding_rate",
            lambda p: p.fetch_funding_rate("BTC/USDT:USDT"),
        ),
        (
            "fetch_ticker",
            lambda p: p.fetch_perp_ticker("BTC/USDT:USDT"),
        ),
    ],
)
def test_every_method_wraps_ccxt_errors_as_data_provider_error(
    monkeypatch, raised, method_name, call,
):

    provider = FundingDataProvider()

    def _raise(*args, **kwargs):
        raise raised

    monkeypatch.setattr(provider._futures_exchange, method_name, _raise)

    with pytest.raises(DataProviderError):

        call(provider)


def test_never_configured_with_api_credentials():
    """
    Belt-and-suspenders alongside the module's static security test
    (mirrors app/execution/live_*.py's) - this class must never be
    capable of authenticated (order-placing) calls.
    """

    provider = FundingDataProvider()

    assert not provider._futures_exchange.apiKey
    assert not provider._futures_exchange.secret
