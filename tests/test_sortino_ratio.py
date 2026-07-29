from app.analytics.sortino_ratio import SortinoRatio


def test_sortino_ratio():

    returns = [
        0.01,
        0.02,
        -0.01,
        0.03,
        0.015,
        -0.005,
        0.02,
    ]

    ratio = SortinoRatio.calculate(returns)

    assert isinstance(ratio, float)