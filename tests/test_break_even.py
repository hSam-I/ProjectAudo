from app.risk.break_even import BreakEven


def test_break_even_moves_stop():

    stop = BreakEven.update(
        entry_price=100,
        current_price=103,
        current_stop=95,
        atr=2,
    )

    assert stop == 100


def test_break_even_not_triggered():

    stop = BreakEven.update(
        entry_price=100,
        current_price=101,
        current_stop=95,
        atr=2,
    )

    assert stop == 95