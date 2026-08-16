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


def test_sortino_ratio_no_downside_positive_mean_is_infinite():

    returns = [0.01, 0.02, 0.03, 0.01]

    assert SortinoRatio.calculate(returns) == float("inf")


def test_sortino_ratio_no_downside_zero_mean_is_zero():

    returns = [0.0, 0.0, 0.0, 0.0]

    assert SortinoRatio.calculate(returns) == 0.0