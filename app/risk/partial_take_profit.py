class PartialTakeProfit:
    """
    Closes half of the position
    after reaching the first target.
    """

    @staticmethod
    def update(
        trade,
        current_price: float,
    ) -> None:

        if trade.partial_tp_taken:
            return

        target = (
            trade.entry_price
            + (
                trade.take_profit
                - trade.entry_price
            ) / 2
        )

        if current_price >= target:

            trade.remaining_quantity *= 0.5

            trade.partial_tp_taken = True