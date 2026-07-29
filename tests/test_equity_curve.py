from app.analytics.equity_curve import EquityCurve


def test_equity_curve():

    history = [
        10000,
        10200,
        10150,
        10500,
        10300,
    ]

    assert EquityCurve.highest(history) == 10500
    assert EquityCurve.lowest(history) == 10000
    assert EquityCurve.final(history) == 10300
    assert EquityCurve.cumulative(history) == history