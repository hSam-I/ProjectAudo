from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.strategy.ema_rsi_strategy import EMARSIStrategy


class Backtester:

    def __init__(self):

        self.strategy = EMARSIStrategy()

        self.portfolio = Portfolio(10000)

    def run(self, df):

        for i in range(50, len(df)):

            history = df.iloc[: i + 1]

            signal = self.strategy.generate_signal(history)

            price = history.iloc[-1]["close"]

            if signal == "BUY":

                trade = Trade(
                    symbol="BTC/USDT",
                    side="BUY",
                    entry_price=price,
                    exit_price=price,
                    quantity=1,
                    profit=0,
                    entry_time=str(history.iloc[-1]["timestamp"]),
                    exit_time=str(history.iloc[-1]["timestamp"]),
                )

                self.portfolio.add_trade(trade)

        return self.portfolio