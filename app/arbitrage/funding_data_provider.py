import ccxt

from app.data.binance_provider import BinanceProvider
from app.data.exceptions import DataProviderError
from app.logging.logger import logger


class FundingDataProvider:
    """
    Funding-rate + perpetual-futures market data for the funding
    arbitrage module. Deliberately separate from DataProvider
    (app/data/provider.py) - funding rate / perp ticker data isn't
    OHLCV-shaped, and BinanceProvider is that ABC's only consumer
    today, so bolting this onto it would be the wrong abstraction.

    Wraps two independent things:
    - the spot leg: an existing BinanceProvider instance (reused as-is,
      same fetch_ohlcv/fetch_ticker, same DataProviderError wrapping)
    - the perpetual leg: this class's own thin ccxt wrapper. ccxt needs
      options={"defaultType": "future"} to address BTC/USDT:USDT -
      a different market than spot BTC/USDT, hence a second exchange
      instance rather than reusing BinanceProvider's.

    Never receives API credentials (matches BinanceProvider) - also
    enforced by the arbitrage module's own static security test
    (mirrors tests/test_live_trader.py's
    test_live_execution_modules_never_reference_real_order_placement).
    """

    def __init__(self, spot_provider: BinanceProvider | None = None):

        self.spot = spot_provider or BinanceProvider()

        self._futures_exchange = ccxt.binance(
            {
                "enableRateLimit": True,
                "options": {
                    "defaultType": "future",
                },
            }
        )

    def _call(self, description: str, fn, *args, **kwargs):
        """
        Shared ccxt error wrapping for every method below - same
        RateLimitExceeded/NetworkError/ExchangeError -> DataProviderError
        mapping BinanceProvider uses, factored out here (unlike
        BinanceProvider) because this class has three call sites
        instead of two.
        """

        try:

            return fn(*args, **kwargs)

        except ccxt.RateLimitExceeded as e:

            logger.error(
                f"Binance rate limit exceeded {description}: {e}"
            )

            raise DataProviderError(
                f"Rate limit exceeded {description}: {e}"
            ) from e

        except ccxt.NetworkError as e:

            logger.error(
                f"Network error {description} from Binance: {e}"
            )

            raise DataProviderError(
                f"Network error {description}: {e}"
            ) from e

        except ccxt.ExchangeError as e:

            logger.error(
                f"Binance rejected the request {description}: {e}"
            )

            raise DataProviderError(
                f"Exchange error {description}: {e}"
            ) from e

    def fetch_funding_rate_history(
        self,
        symbol: str,
        since: int | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Raw ccxt funding-rate-history entries (each has "timestamp" and
        "fundingRate", among other fields) for `symbol` (perpetual
        futures notation, e.g. "BTC/USDT:USDT"). Callers needing more
        than `limit` entries page this themselves via `since`, same as
        BinanceProvider.fetch_ohlcv's callers page candles.
        """

        return self._call(
            f"fetching funding rate history for {symbol}",
            self._futures_exchange.fetch_funding_rate_history,
            symbol,
            since=since,
            limit=limit,
        )

    def fetch_funding_rate(self, symbol: str) -> float:
        """
        The CURRENT (most recently published) funding rate for
        `symbol`, used as an entry sanity-check - refuse to open a new
        position into an already-negative rate.
        """

        data = self._call(
            f"fetching current funding rate for {symbol}",
            self._futures_exchange.fetch_funding_rate,
            symbol,
        )

        return data["fundingRate"]

    def fetch_perp_ticker(self, symbol: str) -> float:
        """
        Last traded price on the perpetual market for `symbol` - used
        for the short leg's fill price and for margin-ratio/basis
        monitoring.
        """

        ticker = self._call(
            f"fetching perpetual ticker for {symbol}",
            self._futures_exchange.fetch_ticker,
            symbol,
        )

        return ticker["last"]
