from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.strategy.ema_rsi_strategy import EMARSIStrategy


class Backtester:
    """
    Executes historical backtests using historical OHLCV data.

    Important:
    Signals are generated on the CLOSE of candle i,
    but trades are executed on the OPEN of candle i+1
    to avoid look-ahead bias.
    """

    def __init__(self):

        self.strategy = EMARSIStrategy()
        self.portfolio = Portfolio(10000)

    def run(self, df):

        current_trade = None

        # We stop at len(df) - 1 because we execute
        # orders on the next candle (i + 1).
        for i in range(50, len(df) - 1):

            history = df.iloc[: i + 1]

            signal = self.strategy.generate_signal(history)

            signal_candle = history.iloc[-1]

            execution_candle = df.iloc[i + 1]

            execution_price = execution_candle["open"]

            execution_time = str(execution_candle["timestamp"])

            # ---------- BUY ----------

            if signal == "BUY" and current_trade is None:

                current_trade = Trade(
                    symbol="BTC/USDT",
                    side="BUY",
                    entry_price=execution_price,
                    quantity=1,
                    entry_time=execution_time,
                )

                self.portfolio.open_trade(current_trade)

            # ---------- SELL ----------

            elif signal == "SELL" and current_trade is not None:

                current_trade.close(
                    exit_price=execution_price,
                    exit_time=execution_time,
                )

                self.portfolio.close_trade(current_trade)

                current_trade = None

        return self.portfolio