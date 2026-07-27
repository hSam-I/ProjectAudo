from app.risk.trailing_stop import TrailingStop


def test_trailing_stop_moves_up():

    stop = TrailingStop.update(
        current_stop=95,
        current_price=110,
        atr=2,
    )

    assert stop == 106


def test_trailing_stop_never_moves_down():

    stop = TrailingStop.update(
        current_stop=106,
        current_price=107,
        atr=2,
    )

    assert stop == 106