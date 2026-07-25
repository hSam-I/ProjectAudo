from app.backtesting.trade import Trade


class Portfolio:

    def __init__(self, initial_balance):

        self.initial_balance = initial_balance

        self.balance = initial_balance

        self.trades = []

    def add_trade(self, trade: Trade):

        self.trades.append(trade)

        self.balance += trade.profit

    @property
    def total_trades(self):

        return len(self.trades)