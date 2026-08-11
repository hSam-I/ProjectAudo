from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # =====================================================
    # ACCOUNT
    # =====================================================

    starting_balance: float = 10_000.0

    leverage: int = 1

    commission: float = 0.001

    slippage: float = 0.0005

    # =====================================================
    # MARKET
    # =====================================================

    symbols: list[str] = [
        "BTC/USDT",
    ]

    timeframe: str = "1h"

    candle_limit: int = 500

    warmup_candles: int = 50

    exchange: str = "binance"

    # =====================================================
    # STRATEGY
    # =====================================================

    strategy: str = "ema_rsi"

    max_open_positions: int = 5

    enable_multi_position: bool = False

    enable_voting: bool = False

    voting_strategies: list[str] = [
        "ema_rsi",
        "breakout",
        "trend_following",
        "mean_reversion",
    ]

    # =====================================================
    # RISK
    # =====================================================

    risk_per_trade: float = 0.01

    max_portfolio_risk: float = 0.05

    stop_loss_atr: float = 2.0

    take_profit_rr: float = 2.0

    trailing_stop_atr: float = 2.0

    break_even_rr: float = 1.0

    partial_tp_rr: float = 1.5

    # =====================================================
    # POSITION SIZING
    # =====================================================

    minimum_position_size: float = 10.0

    maximum_position_size: float = 100000.0

    # =====================================================
    # AI
    # =====================================================

    ai_enabled: bool = True

    minimum_ai_score: int = 20

    minimum_confidence: float = 0.60

    # =====================================================
    # BACKTEST
    # =====================================================

    backtest_initial_cash: float = 10000.0

    backtest_save_reports: bool = True

    # =====================================================
    # OPTIMIZATION
    # =====================================================

    optimization_trials: int = 100

    optimization_metric: str = "profit_factor"

    # =====================================================
    # RESEARCH & WALK-FORWARD
    # =====================================================

    enable_research: bool = False

    walk_forward_train_size: int = 250

    walk_forward_test_size: int = 100

    # =====================================================
    # REPORTING
    # =====================================================

    report_folder: str = "reports"

    log_level: str = "INFO"

    # =====================================================
    # SCHEDULER
    # =====================================================

    scheduler_interval_seconds: int = 60

    # =====================================================
    # LIVE / PAPER TRADING
    # =====================================================

    live_poll_buffer_seconds: int = 10

    enable_live_paper_trading: bool = False

    # =====================================================
    # VALIDATORS
    # =====================================================

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, value):

        if isinstance(value, str):
            return [
                symbol.strip()
                for symbol in value.split(",")
            ]

        return value

    # =====================================================
    # BACKWARD COMPATIBILITY
    # =====================================================

    @property
    def symbol(self) -> str:
        """
        Legacy support.

        Old code:
            settings.symbol

        New code:
            settings.symbols
        """

        return self.symbols[0]


settings = Settings()