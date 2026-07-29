from app.analytics.calmar_ratio import CalmarRatio


def test_calmar_ratio():

    ratio = CalmarRatio.calculate(
        annual_return=25,
        max_drawdown=10,
    )

    assert ratio == 2.5