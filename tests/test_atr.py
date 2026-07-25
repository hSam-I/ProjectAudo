import pandas as pd

from app.indicators.atr import ATR


def test_atr_column_created(sample_market_data):

    result = ATR.calculate(sample_market_data.copy())

    assert "atr" in result.columns


def test_last_atr_not_nan(sample_market_data):

    result = ATR.calculate(sample_market_data.copy())

    assert pd.notna(result.iloc[-1]["atr"])


def test_atr_positive(sample_market_data):

    result = ATR.calculate(sample_market_data.copy())

    assert result.iloc[-1]["atr"] > 0