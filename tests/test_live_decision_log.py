"""
Covers app.execution.live_decision_log.LiveDecisionLog - the
append-only JSONL history of decisions the live loop made, read back
by the status hub's "recent decisions" view.
"""

import json

from app.core.enums import Signal
from app.execution.live_decision_log import LiveDecisionLog
from app.market.regime import MarketRegime


def test_tail_returns_empty_list_when_no_file_exists(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    assert LiveDecisionLog.tail(10) == []


def test_append_and_tail_roundtrip(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    LiveDecisionLog.append(
        timestamp="2024-01-01 00:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.BUY,
        signal=Signal.BUY,
        score=70,
        regime=MarketRegime.RANGING,
    )

    entries = LiveDecisionLog.tail(10)

    assert len(entries) == 1
    assert entries[0]["symbol"] == "BTC/USDT"
    assert entries[0]["raw_signal"] == "BUY"
    assert entries[0]["regime"] == "RANGING"
    assert entries[0]["score"] == 70


def test_regime_enum_is_serialized_as_plain_value_not_repr(tmp_path, monkeypatch):
    """
    MarketRegime is a (str, Enum); json.dump()'ing it directly (rather
    than str()'ing it first) must produce "RANGING", not
    "MarketRegime.RANGING".
    """

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    LiveDecisionLog.append(
        timestamp="2024-01-01 00:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.HOLD,
        signal=Signal.HOLD,
        score=0,
        regime=MarketRegime.RANGING,
    )

    raw_line = LiveDecisionLog.FILE.read_text(encoding="utf-8").strip()

    assert json.loads(raw_line)["regime"] == "RANGING"
    assert "MarketRegime" not in raw_line


def test_tail_returns_newest_first(tmp_path, monkeypatch):

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    for i in range(5):
        LiveDecisionLog.append(
            timestamp=f"2024-01-01 0{i}:00:00",
            symbol="BTC/USDT",
            raw_signal=Signal.HOLD,
            signal=Signal.HOLD,
            score=i,
            regime=MarketRegime.RANGING,
        )

    entries = LiveDecisionLog.tail(3)

    assert [e["score"] for e in entries] == [4, 3, 2]


def test_tail_tolerates_a_truncated_last_line(tmp_path, monkeypatch):
    """
    A crash mid-append can only leave the LAST JSONL line truncated
    (each entry is fully written before the next append starts) -
    tail() must skip it rather than raising.
    """

    file = tmp_path / "decisions.jsonl"
    monkeypatch.setattr(LiveDecisionLog, "FILE", file)

    LiveDecisionLog.append(
        timestamp="2024-01-01 00:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.HOLD,
        signal=Signal.HOLD,
        score=1,
        regime=MarketRegime.RANGING,
    )

    with open(file, "a", encoding="utf-8") as f:
        f.write('{"timestamp": "2024-01-01 01:00:00", "symbol": "BTC/US')

    entries = LiveDecisionLog.tail(10)

    assert len(entries) == 1
    assert entries[0]["score"] == 1


def test_tail_dedupes_by_symbol_and_timestamp_keeping_newest_copy(tmp_path, monkeypatch):
    """
    A restart that reprocesses the last-seen candle can append a
    duplicate (symbol, timestamp) entry - tail() must keep only the
    most recently appended copy.
    """

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    LiveDecisionLog.append(
        timestamp="2024-01-01 00:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.HOLD,
        signal=Signal.HOLD,
        score=1,
        regime=MarketRegime.RANGING,
    )

    LiveDecisionLog.append(
        timestamp="2024-01-01 00:00:00",
        symbol="BTC/USDT",
        raw_signal=Signal.BUY,
        signal=Signal.BUY,
        score=99,
        regime=MarketRegime.RANGING,
    )

    entries = LiveDecisionLog.tail(10)

    assert len(entries) == 1
    assert entries[0]["score"] == 99


def test_tail_reads_across_multiple_blocks_for_large_files(tmp_path, monkeypatch):
    """
    _read_last_lines() seeks backward in fixed-size blocks - this pins
    that it still returns the correct newest-N entries once the file is
    larger than a single block.
    """

    monkeypatch.setattr(LiveDecisionLog, "FILE", tmp_path / "decisions.jsonl")

    for i in range(2000):
        LiveDecisionLog.append(
            timestamp=f"2024-01-01T00:00:{i:04d}",
            symbol="BTC/USDT",
            raw_signal=Signal.HOLD,
            signal=Signal.HOLD,
            score=i,
            regime=MarketRegime.RANGING,
        )

    entries = LiveDecisionLog.tail(5)

    assert [e["score"] for e in entries] == [1999, 1998, 1997, 1996, 1995]
