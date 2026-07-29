from app.analytics.drawdown import DrawdownAnalyzer


def test_drawdown():

    history = [
        10000,
        11000,
        10500,
        9000,
        9500,
        12000,
        11500,
    ]

    assert DrawdownAnalyzer.max_drawdown(history) == 18.18
    assert DrawdownAnalyzer.current_drawdown(history) == 4.17