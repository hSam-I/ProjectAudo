from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceReport:
    """
    Immutable summary of a backtest.
    """

    total_trades: int

    winning_trades: int

    losing_trades: int

    win_rate: float

    profit_factor: float

    expectancy: float

    average_win: float

    average_loss: float

    average_trade: float

    net_profit: float

    gross_profit: float

    gross_loss: float