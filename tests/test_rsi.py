import pandas as pd

from app.indicators.rsi import RSI


def test_rsi_column_created(sample_market_data):

    result = RSI.calculate(sample_market_data.copy())

    assert "rsi" in result.columns


def test_last_rsi_not_nan(sample_market_data):

    result = RSI.calculate(sample_market_data.copy())

    assert pd.notna(result.iloc[-1]["rsi"])


def test_rsi_range(sample_market_data):

    result = RSI.calculate(sample_market_data.copy())

    value = result.iloc[-1]["rsi"]

    assert 0 <= value <= 100