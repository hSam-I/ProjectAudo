from datetime import datetime, timezone

import pandas as pd

_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


def timeframe_to_seconds(timeframe: str) -> int:
    """
    Converts a ccxt-style timeframe string ("1m", "15m", "1h", "4h",
    "1d", "1w") to seconds. Deliberately narrow (no month support,
    ccxt's "1M") since nothing in this codebase's default config uses
    anything coarser than days.
    """

    unit = timeframe[-1]

    if unit not in _UNIT_SECONDS:
        raise ValueError(f"Unsupported timeframe unit: {timeframe!r}")

    amount = int(timeframe[:-1])

    return amount * _UNIT_SECONDS[unit]


def utc_now() -> pd.Timestamp:
    """
    Timezone-naive UTC "now", matching BinanceProvider's
    pd.to_datetime(..., unit="ms") timestamps (also tz-naive UTC).
    """

    return pd.Timestamp(datetime.now(timezone.utc)).tz_localize(None)
