from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.strategy.ema_rsi_strategy import EMARSIStrategy


class Backtester:

    def __init__(self):

        self.strategy = EMARSIStrategy()

        self.portfolio = Portfolio(10000)

    def run(self, df):

        current_trade = None

        for i in range(50, len(df)):

            history = df.iloc[: i + 1]

            signal = self.strategy.generate_signal(history)

            candle = history.iloc[-1]

            price = candle["close"]

            timestamp = str(candle["timestamp"])

            if signal == "BUY" and current_trade is None:

                current_trade = Trade(
                    symbol="BTC/USDT",
                    side="BUY",
                    entry_price=price,
                    quantity=1,
                    entry_time=timestamp,
                )

                self.portfolio.open_trade(current_trade)

            elif signal == "SELL" and current_trade is not None:

                current_trade.close(
                    exit_price=price,
                    exit_time=timestamp,
                )

                self.portfolio.close_trade(current_trade)

                current_trade = None

        return self.portfolio