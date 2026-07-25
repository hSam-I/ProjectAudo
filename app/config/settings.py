from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Exchange
    exchange: str = "binance"

    symbol: str = "BTC/USDT"

    timeframe: str = "1h"

    candle_limit: int = 1000

    # Portfolio
    starting_balance: float = 10000.0

    risk_percent: float = 1.0

    # Strategy
    ema_fast: int = 20

    ema_slow: int = 50

    rsi_period: int = 14

    atr_period: int = 14

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()