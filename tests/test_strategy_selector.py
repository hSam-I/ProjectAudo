from app.ai.strategy_selector import StrategySelector


def test_strategy_selector():

    selector = StrategySelector()

    strategy = selector.select(None)

    assert strategy == "ema_rsi"