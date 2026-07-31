import pandas as pd
import pytest


@pytest.fixture
def sample_market_data():

    rows = []

    price = 100.0

    for i in range(60):

        ema20 = price + 5
        ema50 = price

        rows.append(
            {
                "timestamp": i,
                "open": price,
                "high": price + 2,
                "low": price - 2,
                "close": price + 1,
                "volume": 1000,

                # -----------------------------
                # EMA (legacy)
                # -----------------------------
                "ema_20": ema20,
                "ema_50": ema50,

                # -----------------------------
                # EMA (new compatibility)
                # -----------------------------
                "ema_fast": ema20,
                "ema_slow": ema50,

                # -----------------------------
                # Indicators
                # -----------------------------
                "rsi": 55,
                "macd": 1,
                "macd_signal": 0.5,
                "macd_histogram": 0.5,
                "atr": 2,
                "adx": 30,

                # -----------------------------
                # Market regime flags
                # -----------------------------
                "trend_market": True,
                "bear_market": False,
                "sideways_market": False,
                "high_volatility_market": False,
                "low_volatility_market": False,
                "breakout": False,

                # -----------------------------
                # AI scoring flags
                # -----------------------------
                "macd_bullish": True,
                "volume_spike": False,
                "hammer": False,
            }
        )

        price += 1

    return pd.DataFrame(rows)