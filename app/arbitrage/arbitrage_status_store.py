import json
import os

from app.arbitrage.arbitrage_state_store import ArbitrageStateCorruptError
from app.config.paths import DATA_DIR


class ArbitrageStatusStore:
    """
    Heartbeat for the funding-arbitrage poll loop: poll counters,
    last/next poll timestamps, restart count, and a snapshot of the
    open position's risk (position_status/margin_ratio/
    cumulative_funding, all None when no position is open) - so a
    separate reader (a later CLI/web view) can observe a running loop
    without sharing memory. Pure telemetry, no trading history - a
    corrupt file here is safe to reset (unlike ArbitrageStateStore).
    Same atomic-write pattern as LiveStatusStore.
    """

    FILE = DATA_DIR / "arbitrage_status.json"

    @classmethod
    def save(
        cls,
        *,
        symbol: str,
        started_at,
        restart_count: int,
        last_poll_at,
        next_poll_due_at,
        poll_count: int,
        error_count: int,
        last_error: str | None,
        position_status: str | None,
        margin_ratio: float | None,
        cumulative_funding: float | None,
    ) -> None:

        state = {
            "version": 1,
            "pid": os.getpid(),
            "symbol": symbol,
            "started_at": str(started_at),
            "restart_count": restart_count,
            "last_poll_at": (
                str(last_poll_at) if last_poll_at is not None else None
            ),
            "next_poll_due_at": (
                str(next_poll_due_at)
                if next_poll_due_at is not None
                else None
            ),
            "poll_count": poll_count,
            "error_count": error_count,
            "last_error": last_error,
            "position_status": position_status,
            "margin_ratio": margin_ratio,
            "cumulative_funding": cumulative_funding,
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

            try:
                return json.load(file)

            except json.JSONDecodeError as e:

                raise ArbitrageStateCorruptError(
                    f"{cls.FILE} exists but is not valid JSON "
                    f"(a crash mid-write should be impossible - saves "
                    f"are atomic - so this likely means the file was "
                    f"edited or damaged externally): {e}"
                ) from e
