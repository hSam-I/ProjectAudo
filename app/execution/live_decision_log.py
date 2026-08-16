import json
import os

from app.config.paths import DATA_DIR


class LiveDecisionLog:
    """
    Append-only JSONL history of every decision the live loop made,
    read back by the status hub for a "recent decisions" view.

    tail() seeks from the end of the file instead of reading it whole -
    on a process running for weeks this file only grows, so a full
    read on every hub refresh would get slower over the process's
    entire lifetime for no benefit, since only the last few entries are
    ever displayed.

    A crash mid-append can only ever leave the LAST line truncated (JSONL
    entries are appended one at a time, each fully written before the
    next starts), so tail() tolerates exactly that: an unparsable final
    line is skipped rather than raised. A restart that reprocesses the
    last-seen candle can also append a duplicate (symbol, timestamp)
    entry - tail() drops the older copy at read time rather than trying
    to avoid writing the duplicate in the first place, keeping the
    write path a plain, unconditional append.
    """

    FILE = DATA_DIR / "decisions.jsonl"

    @classmethod
    def append(
        cls,
        *,
        timestamp,
        symbol: str,
        raw_signal,
        signal,
        score,
        regime,
    ) -> None:

        entry = {
            "timestamp": str(timestamp),
            "symbol": symbol,
            "raw_signal": raw_signal,
            "signal": signal,
            "score": score,
            "regime": regime,
        }

        cls.FILE.parent.mkdir(exist_ok=True)

        with open(cls.FILE, "a", encoding="utf-8") as file:
            json.dump(entry, file)
            file.write("\n")

    @classmethod
    def tail(cls, n: int) -> list[dict]:
        """
        Returns up to `n` most recent entries, newest first, deduped by
        (symbol, timestamp) - keeping the most recently appended copy
        of any duplicate.
        """

        if not cls.FILE.exists():
            return []

        raw_lines = cls._read_last_lines(cls.FILE, n)

        deduped: dict[tuple, dict] = {}

        for line in raw_lines:

            line = line.strip()

            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                # Only the last line can be a genuine crash-mid-write
                # truncation (see class docstring) - tolerated the same
                # way for any line, since a bad line elsewhere in the
                # file could otherwise silently swallow the whole tail.
                continue

            key = (entry.get("symbol"), entry.get("timestamp"))

            deduped[key] = entry

        return list(reversed(deduped.values()))

    @staticmethod
    def _read_last_lines(path, n: int) -> list[str]:

        block_size = 8192

        with open(path, "rb") as file:

            file.seek(0, os.SEEK_END)

            remaining = file.tell()

            data = b""
            line_count = 0

            while remaining > 0 and line_count <= n:

                read_size = min(block_size, remaining)

                remaining -= read_size

                file.seek(remaining)

                data = file.read(read_size) + data

                line_count = data.count(b"\n")

        text = data.decode("utf-8", errors="replace")

        # A trailing newline (every append() ends with one) would
        # otherwise leave an empty string as the last split element,
        # pushing the real last line out of the [-n:] slice below.
        if text.endswith("\n"):
            text = text[:-1]

        lines = text.split("\n")

        return lines[-n:]
