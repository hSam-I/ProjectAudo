class TrailingStop:
    """
    Updates the stop-loss as price moves
    in favor of the trade.

    The stop-loss only moves forward.
    It never moves backward.
    """

    @staticmethod
    def update(
        current_stop: float,
        current_price: float,
        atr: float,
        multiplier: float = 2.0,
    ) -> float:

        candidate_stop = current_price - (atr * multiplier)

        return max(current_stop, candidate_stop)