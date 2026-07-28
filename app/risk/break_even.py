class BreakEven:
    """
    Moves stop-loss to entry
    after enough profit.
    """

    @staticmethod
    def update(
        entry_price: float,
        current_price: float,
        current_stop: float,
        atr: float,
        trigger: float = 1.0,
    ) -> float:

        trigger_price = (
            entry_price
            + atr * trigger
        )

        if current_price >= trigger_price:

            return max(
                current_stop,
                entry_price,
            )

        return current_stop