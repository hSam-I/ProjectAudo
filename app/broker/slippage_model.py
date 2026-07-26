class SlippageModel:
    """
    Applies slippage to execution prices.
    """

    def __init__(
        self,
        slippage_rate: float = 0.0005,
    ):

        self.slippage_rate = slippage_rate

    def buy_price(
        self,
        market_price: float,
    ) -> float:

        return market_price * (
            1 + self.slippage_rate
        )

    def sell_price(
        self,
        market_price: float,
    ) -> float:

        return market_price * (
            1 - self.slippage_rate
        )