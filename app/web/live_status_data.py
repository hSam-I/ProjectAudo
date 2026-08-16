import pandas as pd

from app.core.time_utils import utc_now
from app.execution.live_decision_log import LiveDecisionLog
from app.execution.live_state_store import LiveStateCorruptError, LiveStateStore
from app.execution.live_status_store import LiveStatusStore

DECISION_TAIL = 20

# How many recent decisions to fetch for charting (candlestick/score
# time series) - deliberately larger than DECISION_TAIL (the "recent
# decisions" table only needs a handful of rows, the charts want more
# context). A module constant, not a Settings field, matching
# DECISION_TAIL's own precedent: this is a pure display choice, not a
# data-fetch window like settings.candle_limit.
CHART_HISTORY = 100


def load_live_status() -> dict:
    """
    Reads the live loop's on-disk heartbeat/state/decision-history
    files and turns them into a display-ready dict for the /live route
    and the --live-status CLI. Deliberately makes NO network call -
    unlike load_dashboard_data() (which fetches fresh market data),
    this only ever reports what a separate, already-running --live/--web
    process last wrote to disk.

    LiveStateCorruptError is caught here (rather than left to propagate,
    as run_forever() does) because this is a read-only viewer, not the
    live loop itself - it should show a "state is corrupt" message
    instead of crashing the page. FileNotFoundError/PermissionError are
    tolerated too, since a reader can race a concurrent atomic write on
    Windows.
    """

    try:
        status = _read_status()
    except LiveStateCorruptError as e:
        return _corrupt_status(str(e))

    if status is None:
        return _never_run_status()

    health, overdue_by_seconds = _health(status.get("next_poll_due_at"))

    result = {
        "has_run": True,
        "corrupt": False,
        "corrupt_error": None,
        "symbol": status["symbol"],
        "mode": status["mode"],
        "started_at": status["started_at"],
        "restart_count": status["restart_count"],
        "poll_count": status["poll_count"],
        "error_count": status["error_count"],
        "last_error": status["last_error"],
        "last_poll_at": status["last_poll_at"],
        "next_poll_due_at": status["next_poll_due_at"],
        "health": health,
        "overdue_by_seconds": overdue_by_seconds,
        "paper_trading": status["mode"] == "paper",
        "balance": None,
        "open_position_count": None,
        "decisions": [],
        "chart_decisions": [],
    }

    if result["paper_trading"]:

        try:
            paper_state = _read_paper_state()
        except LiveStateCorruptError as e:
            return _corrupt_status(str(e))

        if paper_state is not None:

            result["balance"] = paper_state["balance"]

            result["open_position_count"] = sum(
                1
                for trade in paper_state["trades"]
                if trade["status"] == "OPEN"
            )

    recent = _read_decisions()

    result["decisions"] = recent[:DECISION_TAIL]
    result["chart_decisions"] = _chart_decisions(recent, result["symbol"])

    return result


def _read_status() -> dict | None:

    try:
        return LiveStatusStore.load()
    except (FileNotFoundError, PermissionError):
        return None


def _read_paper_state() -> dict | None:

    try:
        return LiveStateStore.load()
    except (FileNotFoundError, PermissionError):
        return None


def _read_decisions() -> list[dict]:

    try:
        return LiveDecisionLog.tail(CHART_HISTORY)
    except (FileNotFoundError, PermissionError):
        return []


def _chart_decisions(decisions: list[dict], symbol: str | None) -> list[dict]:
    """
    Turns tail()'s newest-first, possibly-multi-symbol result into a
    chronological (oldest-first, left-to-right) series scoped to one
    symbol - decisions.jsonl is a single shared file, so if more than
    one --live process were ever pointed at it, filtering by the
    reporting symbol keeps a candlestick chart from interleaving two
    unrelated instruments.
    """

    scoped = (
        [entry for entry in decisions if entry.get("symbol") == symbol]
        if symbol is not None
        else decisions
    )

    return list(reversed(scoped))


def _health(next_poll_due_at_raw) -> tuple[str, float | None]:

    if next_poll_due_at_raw is None:
        return "NO DATA", None

    next_poll_due_at = pd.Timestamp(next_poll_due_at_raw)

    overdue_seconds = (utc_now() - next_poll_due_at).total_seconds()

    if overdue_seconds > 0:
        return "OVERDUE", overdue_seconds

    return "OK", None


def _never_run_status() -> dict:

    return {
        "has_run": False,
        "corrupt": False,
        "corrupt_error": None,
        "symbol": None,
        "mode": None,
        "started_at": None,
        "restart_count": None,
        "poll_count": None,
        "error_count": None,
        "last_error": None,
        "last_poll_at": None,
        "next_poll_due_at": None,
        "health": "NO DATA",
        "overdue_by_seconds": None,
        "paper_trading": False,
        "balance": None,
        "open_position_count": None,
        "decisions": [],
        "chart_decisions": [],
    }


def _corrupt_status(error: str) -> dict:

    state = _never_run_status()

    state["has_run"] = True
    state["corrupt"] = True
    state["corrupt_error"] = error

    return state
