from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade
from app.broker.paper_broker import PaperBroker
from app.config.settings import settings
from app.core.enums import OrderSide
from app.core.enums import Signal
from app.decision.decision_engine import DecisionEngine
from app.risk.position_sizer import PositionSizer
from app.risk.risk_manager import RiskManager
from app.strategy.base_strategy import BaseStrategy


class Backtester:
    """
    Historical backtesting engine.

    Signals are generated on candle i (close),
    but executed on candle i+1 (open).

    This avoids look-ahead bias.
    """

    def __init__(
        self,
        strategy: BaseStrategy | None = None,
    ):

        self.portfolio = Portfolio(settings.starting_balance)

        self.broker = PaperBroker(self.portfolio)

        self.risk_manager = RiskManager()

        self.decision_engine = DecisionEngine(
            strategy=strategy,
        )

    def run(self, df):

        current_trade = None

        for i in range(50, len(df) - 1):

            history = df.iloc[: i + 1]

            decision = self.decision_engine.evaluate(history)

            signal = decision.signal

            execution_candle = df.iloc[i + 1]

            current_high = execution_candle["high"]
            current_low = execution_candle["low"]

            entry_price = execution_candle["open"]
            entry_time = str(execution_candle["timestamp"])

            atr = history.iloc[-1]["atr"]

            # ====================================================
            # OPEN POSITION MANAGEMENT
            # ====================================================

            if current_trade is not None:

                if current_low <= current_trade.stop_loss:

                    current_trade.close(
                        exit_price=current_trade.stop_loss,
                        exit_time=entry_time,
                        reason="STOP_LOSS",
                    )

                    self.broker.close(current_trade)

                    current_trade = None

                    continue

                if current_high >= current_trade.take_profit:

                    current_trade.close(
                        exit_price=current_trade.take_profit,
                        exit_time=entry_time,
                        reason="TAKE_PROFIT",
                    )

                    self.broker.close(current_trade)

                    current_trade = None

                    continue

            # ====================================================
            # BUY
            # ====================================================

            if signal == Signal.BUY and current_trade is None:

                risk_amount = self.risk_manager.risk_amount(
                    self.portfolio.balance
                )

                stop_loss = self.risk_manager.stop_loss(
                    entry_price,
                    atr,
                )

                take_profit = self.risk_manager.take_profit(
                    entry_price,
                    atr,
                )

                stop_loss_distance = (
                    self.risk_manager.stop_loss_distance(
                        atr
                    )
                )

                quantity = PositionSizer.calculate_position_size(
                    balance=self.portfolio.balance,
                    risk_amount=risk_amount,
                    stop_loss_distance=stop_loss_distance,
                )

                current_trade = Trade(
                    symbol=settings.symbol,
                    side=OrderSide.BUY,
                    entry_price=entry_price,
                    quantity=quantity,
                    entry_time=entry_time,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_amount=risk_amount,
                )

                self.broker.buy(current_trade)

            # ====================================================
            # SELL
            # ====================================================

            elif (
                signal == Signal.SELL
                and current_trade is not None
            ):

                current_trade.close(
                    exit_price=entry_price,
                    exit_time=entry_time,
                    reason="SIGNAL",
                )

                self.broker.close(current_trade)

                current_trade = None

        return self.portfolio