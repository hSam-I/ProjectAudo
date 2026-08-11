import dataclasses
import json
import os
from pathlib import Path

import pandas as pd

from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.core.enums import OrderSide
from app.portfolio.portfolio_manager import PortfolioManager


class LiveStateStore:
    """
    Persists a live paper-trading Portfolio's balance/trades and the
    last processed candle timestamp to disk, so a restarted process
    resumes instead of starting fresh.

    Same flat-JSON approach as PerformanceDatabase, but with an atomic
    write (temp file + os.replace()) - PerformanceDatabase itself was
    missing this and has now been fixed too (see
    app/analytics/performance_db.py), but this store was written
    correctly from the start since it's new code.
    """

    FILE = Path("data/live_state.json")

    @classmethod
    def save(
        cls,
        portfolio: Portfolio,
        last_processed_timestamp,
    ) -> None:

        state = {
            "initial_balance": portfolio.initial_balance,
            "balance": portfolio.balance,
            "balance_history": portfolio.balance_history,
            "trades": [
                dataclasses.asdict(trade)
                for trade in portfolio.trades
            ],
            "last_processed_timestamp": (
                str(last_processed_timestamp)
                if last_processed_timestamp is not None
                else None
            ),
        }

        cls.FILE.parent.mkdir(exist_ok=True)

        temp_path = cls.FILE.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)

        os.replace(temp_path, cls.FILE)

    @classmethod
    def load(cls) -> dict | None:

        if not cls.FILE.exists():
            return None

        with open(cls.FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def restore_into(
        cls,
        portfolio: Portfolio,
        portfolio_manager: PortfolioManager,
    ) -> pd.Timestamp | None:
        """
        Mutates portfolio/portfolio_manager IN PLACE from saved state -
        never replaces the object references. Backtester's PaperBroker
        is constructed with a reference to this exact `portfolio`
        object; swapping that reference out from under it (rather than
        mutating it) would leave the broker writing to a stale,
        disconnected Portfolio while callers see the restored one.

        Returns the saved last_processed_timestamp, or None if there
        was no saved state to restore.
        """

        state = cls.load()

        if state is None:
            return None

        portfolio.initial_balance = state["initial_balance"]
        portfolio.balance = state["balance"]
        portfolio.balance_history = state["balance_history"]

        trades = [
            Trade(
                **{
                    **trade_data,
                    "side": OrderSide(trade_data["side"]),
                }
            )
            for trade_data in state["trades"]
        ]

        portfolio.trades = trades

        portfolio.closed_trades = [
            trade
            for trade in trades
            if trade.status == "CLOSED"
        ]

        portfolio.open_positions = [
            trade
            for trade in trades
            if trade.status == "OPEN"
        ]

        for trade in portfolio.open_positions:
            portfolio_manager.register_trade(trade)

        timestamp = state["last_processed_timestamp"]

        return pd.Timestamp(timestamp) if timestamp else None
