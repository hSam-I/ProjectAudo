import pandas as pd

from app.indicators.ema import EMA


def test_ema_column_created(sample_market_data):

    result = EMA.calculate(sample_market_data.copy(), period=3)

    assert "ema_3" in result.columns


def test_last_ema_is_not_nan(sample_market_data):

    result = EMA.calculate(sample_market_data.copy(), period=3)

    assert pd.notna(result.iloc[-1]["ema_3"])


def test_ema_increasing_market(sample_market_data):

    result = EMA.calculate(sample_market_data.copy(), period=3)

    ema = result.iloc[-1]["ema_3"]

    assert ema > 0