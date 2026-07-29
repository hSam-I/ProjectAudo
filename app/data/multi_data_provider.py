from app.data.binance_provider import BinanceProvider


class MultiDataProvider:
    """
    Fetches market data for multiple symbols.
    """

    def __init__(self):

        self.provider = BinanceProvider()

    def fetch_all(
        self,
        symbols: list[str],
        timeframe: str,
        limit: int = 500,
    ) -> dict:

        market_data = {}

        for symbol in symbols:

            market_data[symbol] = (
                self.provider.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                )
            )

        return market_data