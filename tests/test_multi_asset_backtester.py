from app.backtesting.multi_asset_backtester import MultiAssetBacktester


def test_create():

    engine = MultiAssetBacktester()

    assert engine is not None