import pytest

from app.strategy.ema_rsi_strategy import EMARSIStrategy
from app.strategy.registry import get_strategy


def test_registry_returns_strategy():

    strategy = get_strategy("ema_rsi")

    assert isinstance(
        strategy,
        EMARSIStrategy,
    )


def test_registry_unknown_strategy():

    with pytest.raises(ValueError):

        get_strategy("unknown")