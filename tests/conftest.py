import pandas as pd
import pytest


@pytest.fixture
def sample_market_data():

    rows = []

    price = 100.0

    for i in range(60):

        rows.append(
            {
                "timestamp": i,
                "open": price,
                "high": price + 2,
                "low": price - 2,
                "close": price + 1,
                "volume": 1000,

                # Indicators
                "ema_20": price + 5,
                "ema_50": price,
                "rsi": 55,

                "macd": 1,
                "macd_histogram": 0.5,

                "atr": 2,
            }
        )

        price += 1

    return pd.DataFrame(rows)