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
