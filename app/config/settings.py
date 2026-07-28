from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.

    Values can be overridden using the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==================================================
    # GENERAL
    # ==================================================

    starting_balance: float = 10000.0

    symbol: str = "BTC/USDT"

    timeframe: str = "1h"

    strategy: str = "ema_rsi"

    # ==================================================
    # RISK MANAGEMENT
    # ==================================================

    risk_per_trade: float = 0.01

    max_open_positions: int = 5

    max_portfolio_risk: float = 0.05

    # ==================================================
    # BROKER
    # ==================================================

    fee_rate: float = 0.001

    slippage_rate: float = 0.0005

    # ==================================================
    # BACKTEST
    # ==================================================

    warmup_candles: int = 50


settings = Settings()