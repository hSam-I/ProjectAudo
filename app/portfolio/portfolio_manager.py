from app.backtesting.trade import Trade


class PortfolioManager:
    """
    Manages currently open positions.
    """

    def __init__(self):

        self.positions: dict[str, Trade] = {}

    def can_open_trade(
        self,
        symbol: str,
    ) -> bool:

        return symbol not in self.positions

    def register_trade(
        self,
        trade: Trade,
    ) -> None:

        self.positions[trade.symbol] = trade

    def close_trade(
        self,
        trade: Trade,
    ) -> None:

        self.positions.pop(
            trade.symbol,
            None,
        )

    def get_position(
        self,
        symbol: str,
    ) -> Trade | None:

        return self.positions.get(symbol)

    def open_positions(self) -> list[Trade]:

        return list(self.positions.values())

    def has_position(
        self,
        symbol: str,
    ) -> bool:

        return symbol in self.positions

    def count(self) -> int:

        return len(self.positions)

    def total_exposure(self) -> float:

        return sum(
            trade.entry_price * trade.quantity
            for trade in self.positions.values()
        )

    def clear(self) -> None:

        self.positions.clear()