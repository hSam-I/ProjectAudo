import random

import pandas as pd
import pytest


@pytest.fixture
def random_walk_ohlcv():
    """
    Factory for deterministic (fixed-seed) choppy random-walk
    OHLCV data.

    A monotonic trend saturates RSI long before a slow-moving
    EMA can cross a fast one, so EMA/RSI crossover strategies
    never fire on it. A choppy walk keeps RSI oscillating while
    still producing real EMA crossovers, so it's used wherever
    tests need a strategy to actually trade.
    """

    def _build(
        n: int = 500,
        seed: int = 0,
        amplitude: float = 1.0,
        start_price: float = 200.0,
    ) -> pd.DataFrame:

        rng = random.Random(seed)

        start = pd.Timestamp("2024-01-01")

        rows = []

        price = start_price

        for i in range(n):

            open_ = price

            price += rng.uniform(-amplitude, amplitude)

            close = price

            high = max(open_, close) + rng.uniform(0, amplitude * 0.3)
            low = min(open_, close) - rng.uniform(0, amplitude * 0.3)

            rows.append(
                {
                    "timestamp": start + pd.Timedelta(hours=i),
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + (i % 50) * 10,
                }
            )

        return pd.DataFrame(rows)

    return _build


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