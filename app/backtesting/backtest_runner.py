from app.indicators.indicator_engine import IndicatorEngine
from app.strategy.strategy_factory import StrategyFactory


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

        strategy = StrategyFactory.create(
            parameters,
        )

        df = IndicatorEngine.prepare(
            df=df,
            ema_fast=strategy.ema_fast,
            ema_slow=strategy.ema_slow,
        )

        return df, strategy