"""
Covers app.main.run_live_status() - a one-shot console summary built
on the same load_live_status() read layer the /live web route uses.
load_live_status() itself is monkeypatched throughout (its own
behavior is covered by tests/test_live_status_data.py), so these tests
only check run_live_status()'s console formatting/branching.
"""

import app.main as main_module


def _status(**overrides):

    base = {
        "has_run": True,
        "corrupt": False,
        "corrupt_error": None,
        "symbol": "BTC/USDT",
        "mode": "observe",
        "started_at": "2024-01-01 00:00:00",
        "restart_count": 0,
        "poll_count": 5,
        "error_count": 0,
        "last_error": None,
        "last_poll_at": "2024-01-01 05:00:00",
        "next_poll_due_at": "2024-01-01 06:00:00",
        "health": "OK",
        "overdue_by_seconds": None,
        "paper_trading": False,
        "balance": None,
        "open_position_count": None,
        "decisions": [],
    }

    base.update(overrides)

    return base


def test_never_run_prints_a_clear_message(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(has_run=False),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "No live process has run yet" in output
    assert "--live" in output


def test_corrupt_state_prints_the_error_instead_of_crashing(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(corrupt=True, corrupt_error="simulated corruption"),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "corrupt" in output.lower()
    assert "simulated corruption" in output


def test_healthy_observe_mode_prints_status_fields(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "BTC/USDT" in output
    assert "observe" in output
    assert "Health           : OK" in output
    assert "Observation mode" in output


def test_overdue_health_shows_seconds_in_output(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(health="OVERDUE", overdue_by_seconds=125.4),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "OVERDUE" in output
    assert "125" in output


def test_paper_trading_mode_prints_balance_and_open_positions(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(
            mode="paper",
            paper_trading=True,
            balance=10450.5,
            open_position_count=2,
        ),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "10,450.50" in output
    assert "Open Positions   : 2" in output


def test_decisions_are_printed_when_present(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(
            decisions=[
                {
                    "timestamp": "2024-01-01 05:00:00",
                    "symbol": "BTC/USDT",
                    "raw_signal": "BUY",
                    "signal": "BUY",
                    "score": 70,
                    "regime": "RANGING",
                },
            ],
        ),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "raw=BUY" in output
    assert "final=BUY" in output


def test_no_decisions_prints_a_placeholder(monkeypatch, capsys):

    monkeypatch.setattr(
        main_module,
        "load_live_status",
        lambda: _status(decisions=[]),
    )

    main_module.run_live_status()

    output = capsys.readouterr().out

    assert "(none logged yet)" in output
