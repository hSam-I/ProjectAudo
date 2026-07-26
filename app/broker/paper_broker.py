from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.broker.execution_engine import ExecutionEngine
from app.broker.fee_model import FeeModel
from app.broker.slippage_model import SlippageModel
from app.execution.order_book import OrderBook


class PaperBroker:
    """
    Simulates a broker.

    Used for paper trading before
    connecting to a real exchange.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        fee_rate: float = 0.001,
        slippage: float = 0.0005,
    ):

        self.portfolio = portfolio

        self.order_book = OrderBook()

        self.fee_model = FeeModel(
            fee_rate=fee_rate,
        )

        self.slippage_model = SlippageModel(
            slippage_rate=slippage,
        )

        self.execution_engine = ExecutionEngine(
            portfolio=self.portfolio,
            fee_model=self.fee_model,
            slippage_model=self.slippage_model,
            order_book=self.order_book,
        )

    def buy(
        self,
        trade: Trade,
    ):

        self.execution_engine.execute_buy(
            trade
        )

    def process_market_price(
        self,
        market_price: float,
        timestamp: str,
    ):

        self.execution_engine.process_market_price(
            market_price=market_price,
            timestamp=timestamp,
        )

    def close(
        self,
        trade: Trade,
    ):

        self.execution_engine.execute_sell(
            trade
        )