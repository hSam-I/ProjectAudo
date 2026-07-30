import pandas as pd

from app.core.indicator_accessor import IndicatorAccessor


def test_accessor_new_names():

    row = pd.Series(
        {
            "ema_fast": 110,
            "ema_slow": 100,
        }
    )

    assert IndicatorAccessor.ema_fast(row) == 110
    assert IndicatorAccessor.ema_slow(row) == 100


def test_accessor_old_names():

    row = pd.Series(
        {
            "ema_20": 110,
            "ema_50": 100,
        }
    )

    assert IndicatorAccessor.ema_fast(row) == 110
    assert IndicatorAccessor.ema_slow(row) == 100