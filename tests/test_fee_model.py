from app.broker.fee_model import FeeModel


def test_fee_model():

    model = FeeModel(
        fee_rate=0.001,
    )

    fee = model.calculate(
        price=100,
        quantity=2,
    )

    assert fee == 0.2