from app.backtesting.multi_asset_backtester import (
    MultiAssetBacktester,
)


class Scheduler:
    """
    Runs trading cycles.
    """

    def __init__(self):

        self.engine = MultiAssetBacktester()

    def run_once(self):

        return self.engine.scan()