from app.market.regime import MarketRegime
from app.strategy.strategy_selector_v2 import StrategySelectorV2
from app.strategy.trend_following_strategy import TrendFollowingStrategy


def test_strategy_selector():

    strategy = StrategySelectorV2.choose(
        MarketRegime.TRENDING_BULL
    )

    assert isinstance(
        strategy,
        TrendFollowingStrategy,
    )