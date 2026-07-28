class TrailingStop:
    """
    ATR based trailing stop.
    """

    @staticmethod
    def update(
        current_stop: float,
        current_price: float,
        atr: float,
        multiplier: float = 2.0,
    ) -> float:

        candidate_stop = (
            current_price
            - atr * multiplier
        )

        return max(
            current_stop,
            candidate_stop,
        )