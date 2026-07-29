from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    starting_balance: float = 10000

    risk_per_trade: float = 0.01

    symbols: list[str] = [
        "BTC/USDT",
    ]

    timeframe: str = "1h"

    strategy: str = "ema_rsi"

    warmup_candles: int = 50

    max_open_positions: int = 5

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, value):

        if isinstance(value, str):
            return [
                symbol.strip()
                for symbol in value.split(",")
            ]

        return value


settings = Settings()