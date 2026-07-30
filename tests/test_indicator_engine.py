import pandas as pd

from app.indicators.indicator_engine import IndicatorEngine


def test_indicator_engine():

    df = pd.DataFrame(
        {
            "close": list(range(1, 101)),
        }
    )

    result = IndicatorEngine.prepare(
        df,
        ema_fast=10,
        ema_slow=30,
    )

    assert "ema_fast" in result.columns
    assert "ema_slow" in result.columns

    assert len(result) == 100