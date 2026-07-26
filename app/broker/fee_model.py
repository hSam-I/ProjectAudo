class FeeModel:
    """
    Calculates trading fees.
    """

    def __init__(
        self,
        fee_rate: float = 0.001,
    ):

        self.fee_rate = fee_rate

    def calculate(
        self,
        price: float,
        quantity: float,
    ) -> float:

        return (
            price
            * quantity
            * self.fee_rate
        )