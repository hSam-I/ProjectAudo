class PositionSizer:

    @staticmethod
    def calculate_position_size(
        balance: float,
        risk_amount: float,
        stop_loss_distance: float,
    ):

        return risk_amount / stop_loss_distance