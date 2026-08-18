from app.config.settings import settings


def test_default_strategy():

    assert settings.strategy == "ema_rsi"


def test_funding_arbitrage_defaults_are_opt_in_and_safe():

    assert settings.enable_funding_arbitrage is False
    assert settings.funding_arb_symbol == "BTC/USDT"

    # Safe end of the leverage/liquidation-buffer tradeoff by default -
    # see the funding-arbitrage plan for the measured buffer table.
    assert settings.funding_arb_leverage == 1

    assert settings.funding_arb_maintenance_margin_rate == 0.004
    assert settings.funding_arb_liquidation_warning_pct == 0.5

    # Comfortably above the worst historical negative-funding streak
    # measured (24-25 periods) - a circuit breaker, not a routine
    # trigger.
    assert settings.funding_arb_max_negative_streak == 40

    assert settings.funding_arb_futures_fee == 0.0005
    assert settings.funding_arb_poll_buffer_seconds == 10