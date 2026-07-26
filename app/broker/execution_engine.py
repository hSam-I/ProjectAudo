from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.broker.fee_model import FeeModel
from app.broker.slippage_model import SlippageModel
from app.execution.order import Order
from app.execution.order_book import OrderBook


class ExecutionEngine:
    """
    Handles order execution.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        fee_model: FeeModel,
        slippage_model: SlippageModel,
        order_book: OrderBook,
    ):

        self.portfolio = portfolio

        self.fee_model = fee_model

        self.slippage_model = slippage_model

        self.order_book = order_book

    def execute_buy(
        self,
        trade: Trade,
    ):

        execution_price = self.slippage_model.buy_price(
            trade.entry_price
        )

        order = Order(
            symbol=trade.symbol,
            side=trade.side,
            order_type="MARKET",
            quantity=trade.quantity,
            price=trade.entry_price,
            timestamp=trade.entry_time,
        )

        self.order_book.add(order)

        order.fill(
            price=execution_price,
            timestamp=trade.entry_time,
        )

        trade.entry_price = execution_price

        fee = self.fee_model.calculate(
            price=execution_price,
            quantity=trade.quantity,
        )

        self.portfolio.balance -= fee

        self.portfolio.open_trade(trade)

    def execute_sell(
        self,
        trade: Trade,
    ):

        execution_price = self.slippage_model.sell_price(
            trade.exit_price
        )

        trade.exit_price = execution_price

        fee = self.fee_model.calculate(
            price=execution_price,
            quantity=trade.quantity,
        )

        self.portfolio.balance -= fee

        self.portfolio.close_trade(trade)

    def process_market_price(
        self,
        market_price: float,
        timestamp: str,
    ):

        for order in self.order_book.pending():

            if order.can_fill(market_price):

                order.fill(
                    price=market_price,
                    timestamp=timestamp,
                )