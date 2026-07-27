from app.config.settings import settings


def test_default_strategy():

    assert settings.strategy == "ema_rsi"