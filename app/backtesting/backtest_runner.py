from app.indicators.indicator_engine import IndicatorEngine
from app.strategy.trend_following_strategy import TrendFollowingStrategy


class BacktestRunner:
    """
    Prepares indicators and strategy
    before a backtest starts.
    """

    @staticmethod
    def prepare(
        df,
        parameters: dict,
    ):

        ema_fast = parameters.get("ema_fast", 20)
        ema_slow = parameters.get("ema_slow", 50)

        strategy = TrendFollowingStrategy(
            ema_fast=ema_fast,
            ema_slow=ema_slow,
        )

        df = IndicatorEngine.prepare(
            df=df,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
        )

        return df, strategy