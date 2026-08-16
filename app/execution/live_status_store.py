import json
import os

from app.config.paths import DATA_DIR
from app.execution.live_state_store import LiveStateCorruptError


class LiveStatusStore:
    """
    Persists a heartbeat for the running live loop (--live/--web read
    this the same way --live-status does): poll counters, the last/next
    poll timestamps, and a running restart count - so a process on one
    machine can be observed from a completely separate reader without
    sharing memory.

    Same atomic write approach as LiveStateStore (temp file + os.replace()).
    A fixed ".tmp" suffix is fine here - this store has exactly one
    writer (the live loop itself), so there's no concurrent-writer
    collision to guard against with a randomized temp name.
    """

    FILE = DATA_DIR / "live_status.json"

    @classmethod
    def save(
        cls,
        *,
        symbol: str,
        mode: str,
        started_at,
        restart_count: int,
        last_poll_at,
        next_poll_due_at,
        poll_count: int,
        error_count: int,
        last_error: str | None,
    ) -> None:

        state = {
            "version": 1,
            "pid": os.getpid(),
            "symbol": symbol,
            "mode": mode,
            "started_at": str(started_at),
            "restart_count": restart_count,
            "last_poll_at": (
                str(last_poll_at) if last_poll_at is not None else None
            ),
            "next_poll_due_at": (
                str(next_poll_due_at) if next_poll_due_at is not None else None
            ),
            "poll_count": poll_count,
            "error_count": error_count,
            "last_error": last_error,
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

                raise LiveStateCorruptError(
                    f"{cls.FILE} exists but is not valid JSON "
                    f"(a crash mid-write should be impossible - saves "
                    f"are atomic - so this likely means the file was "
                    f"edited or damaged externally): {e}"
                ) from e
