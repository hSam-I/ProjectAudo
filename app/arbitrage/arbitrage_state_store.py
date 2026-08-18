import dataclasses
import json
import os

from app.arbitrage.position import ArbitragePosition
from app.config.paths import DATA_DIR


class ArbitrageStateCorruptError(Exception):
    """
    Raised when arbitrage_state.json or arbitrage_status.json exists
    but cannot be parsed as JSON. When it comes from
    ArbitrageStateStore (which carries the real funding-collection
    history: cumulative_funding, funding_events, closed positions),
    callers must NEVER catch-and-reset - silently starting fresh would
    discard months of paper-trading history without anyone noticing.
    When it comes from ArbitrageStatusStore (pure heartbeat, no trading
    history), resetting is safe - see FundingArbitrageTrader.__init__
    for both call sites.
    """


class ArbitrageStateStore:
    """
    Persists the currently open ArbitragePosition (or None) plus a
    history of closed positions, so a restarted process resumes
    tracking instead of losing months of accumulated funding history.
    Same atomic-write pattern (temp file + os.replace()) as
    LiveStateStore/LiveStatusStore in app/execution/ - deliberately
    reimplemented here rather than imported, keeping app/arbitrage/
    fully independent of the live-trading module (see the funding-
    arbitrage plan).
    """

    FILE = DATA_DIR / "arbitrage_state.json"

    @classmethod
    def save(
        cls,
        position: ArbitragePosition | None,
        closed_positions: list,
    ) -> None:

        state = {
            "position": (
                dataclasses.asdict(position)
                if position is not None
                else None
            ),
            "closed_positions": [
                dataclasses.asdict(p) for p in closed_positions
            ],
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

    @classmethod
    def restore(cls) -> tuple:
        """
        Returns (position, closed_positions) reconstructed from disk,
        or (None, []) if there is no saved state. Reconstructs
        ArbitragePosition dataclass instances (not raw dicts) so
        callers get the same type they'd get from ArbitrageExecutor.
        """

        state = cls.load()

        if state is None:
            return None, []

        position = (
            ArbitragePosition(**state["position"])
            if state.get("position") is not None
            else None
        )

        closed_positions = [
            ArbitragePosition(**p)
            for p in state.get("closed_positions", [])
        ]

        return position, closed_positions
