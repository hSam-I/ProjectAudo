class PositionSizer:
    """
    Calculates the position size based on
    account risk and stop-loss distance.
    """

    @staticmethod
    def calculate_position_size(
        balance: float,
        risk_amount: float,
        stop_loss_distance: float,
    ) -> float:

        if stop_loss_distance <= 0:
            raise ValueError("Stop-loss distance must be greater than zero.")

        return risk_amount / stop_loss_distance