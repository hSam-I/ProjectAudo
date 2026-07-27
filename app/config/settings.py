from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    starting_balance: float = 10000

    risk_per_trade: float = 0.01

    symbol: str = "BTC/USDT"

    timeframe: str = "1h"

    strategy: str = "ema_rsi"


settings = Settings()