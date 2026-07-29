from app.config.settings import settings
from app.data.multi_data_provider import MultiDataProvider
from app.scanner.market_scanner import MarketScanner


class MultiAssetBacktester:
    """
    Runs backtests for multiple symbols.
    """

    def __init__(self, strategy=None):

        self.data_provider = MultiDataProvider()

        self.scanner = MarketScanner(
            strategy=strategy,
        )

    def load_market_data(self):

        return self.data_provider.fetch_all(
            symbols=settings.symbols,
            timeframe=settings.timeframe,
        )

    def scan(self):

        market_data = self.load_market_data()

        return self.scanner.scan(
            market_data
        )