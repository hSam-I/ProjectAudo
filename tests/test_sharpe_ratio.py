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