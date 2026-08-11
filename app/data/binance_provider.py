import ccxt
import pandas as pd

from app.data.exceptions import DataProviderError
from app.data.provider import DataProvider
from app.logging.logger import logger


class BinanceProvider(DataProvider):
    def __init__(self):
        self.exchange = ccxt.binance(
            {
                "enableRateLimit": True,
            }
        )

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> pd.DataFrame:

        try:

            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit,
            )

        except ccxt.RateLimitExceeded as e:

            logger.error(
                f"Binance rate limit exceeded fetching "
                f"{symbol} {timeframe}: {e}"
            )

            raise DataProviderError(
                f"Rate limit exceeded fetching {symbol}: {e}"
            ) from e

        except ccxt.NetworkError as e:

            logger.error(
                f"Network error fetching {symbol} {timeframe} "
                f"from Binance: {e}"
            )

            raise DataProviderError(
                f"Network error fetching {symbol}: {e}"
            ) from e

        except ccxt.ExchangeError as e:

            logger.error(
                f"Binance rejected the request for "
                f"{symbol} {timeframe}: {e}"
            )

            raise DataProviderError(
                f"Exchange error fetching {symbol}: {e}"
            ) from e

        df = pd.DataFrame(
            ohlcv,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="ms",
        )

        return df

    def fetch_ticker(
        self,
        symbol: str,
    ) -> float:
        """
        Last traded price for symbol, used by live paper trading to
        fill at a real-time price instead of a candle's (possibly
        stale) close - see app/execution/live_trader.py.
        """

        try:

            ticker = self.exchange.fetch_ticker(symbol)

        except ccxt.RateLimitExceeded as e:

            logger.error(
                f"Binance rate limit exceeded fetching ticker "
                f"for {symbol}: {e}"
            )

            raise DataProviderError(
                f"Rate limit exceeded fetching ticker for {symbol}: {e}"
            ) from e

        except ccxt.NetworkError as e:

            logger.error(
                f"Network error fetching ticker for {symbol} "
                f"from Binance: {e}"
            )

            raise DataProviderError(
                f"Network error fetching ticker for {symbol}: {e}"
            ) from e

        except ccxt.ExchangeError as e:

            logger.error(
                f"Binance rejected the ticker request for {symbol}: {e}"
            )

            raise DataProviderError(
                f"Exchange error fetching ticker for {symbol}: {e}"
            ) from e

        return ticker["last"]
