from app.broker.slippage_model import SlippageModel


def test_slippage_model():

    model = SlippageModel(
        slippage_rate=0.001,
    )

    buy = model.buy_price(100)

    sell = model.sell_price(100)

    assert buy == 100.1

    assert sell == 99.9