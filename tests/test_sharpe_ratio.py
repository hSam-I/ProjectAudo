from app.analytics.sharpe_ratio import SharpeRatio


def test_sharpe_ratio():

    returns = [
        0.01,
        0.02,
        -0.01,
        0.03,
        0.01,
        -0.005,
        0.02,
    ]

    sharpe = SharpeRatio.calculate(returns)

    assert isinstance(sharpe, float)


def test_sharpe_ratio_zero_variance_positive_mean_is_infinite():

    returns = [0.01, 0.01, 0.01, 0.01]

    assert SharpeRatio.calculate(returns) == float("inf")


def test_sharpe_ratio_zero_variance_negative_mean_is_negative_infinite():

    returns = [-0.01, -0.01, -0.01, -0.01]

    assert SharpeRatio.calculate(returns) == float("-inf")


def test_sharpe_ratio_zero_variance_zero_mean_is_zero():

    returns = [0.0, 0.0, 0.0, 0.0]

    assert SharpeRatio.calculate(returns) == 0.0