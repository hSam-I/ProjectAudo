from app.strategy.trend_following_strategy import (
    TrendFollowingStrategy,
)


class StrategyFactory:
    """
    Creates strategy instances.
    """

    @staticmethod
    def create(
        parameters: dict | None = None,
    ):

        parameters = parameters or {}

        return TrendFollowingStrategy(
            ema_fast=parameters.get(
                "ema_fast",
                20,
            ),
            ema_slow=parameters.get(
                "ema_slow",
                50,
            ),
            rsi_buy=parameters.get(
                "rsi_buy",
                55,
            ),
            rsi_sell=parameters.get(
                "rsi_sell",
                45,
            ),
        )