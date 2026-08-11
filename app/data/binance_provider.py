import ccxt
import pandas as pd

from app.data.provider import DataProvider
from app.logging.logger import logger

OHLCV_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


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
        """
        Fetches OHLCV candles from Binance.

        Returns an empty DataFrame (instead of raising) on any
        network/exchange failure, so DataValidator can reject it
        the same way it rejects any other unusable response.
        """

        try:

            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit,
            )

        except ccxt.RateLimitExceeded as e:

            logger.error(
                f"Binance rate limit exceeded for {symbol}: {e}"
            )

            return pd.DataFrame(columns=OHLCV_COLUMNS)

        except ccxt.NetworkError as e:

            logger.error(
                f"Network error fetching {symbol} from Binance: {e}"
            )

            return pd.DataFrame(columns=OHLCV_COLUMNS)

        except ccxt.ExchangeError as e:

            logger.error(
                f"Exchange error fetching {symbol} from Binance: {e}"
            )

            return pd.DataFrame(columns=OHLCV_COLUMNS)

        if not ohlcv:

            logger.warning(
                f"Binance returned no candles for {symbol}"
            )

            return pd.DataFrame(columns=OHLCV_COLUMNS)

        df = pd.DataFrame(
            ohlcv,
            columns=OHLCV_COLUMNS,
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="ms",
        )

        return df