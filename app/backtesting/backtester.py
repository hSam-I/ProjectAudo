from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade

from app.broker.paper_broker import PaperBroker

from app.config.settings import settings

from app.core.enums import OrderSide
from app.core.enums import Signal

from app.decision.decision_engine import DecisionEngine

from app.indicators.indicator_engine import IndicatorEngine

from app.logging.logger import logger

from app.risk.portfolio_risk_manager import PortfolioRiskManager
from app.risk.position_manager import PositionManager
from app.risk.position_sizer import PositionSizer
from app.risk.risk_manager import RiskManager

from app.strategy.base_strategy import BaseStrategy


class Backtester:
    """
    Historical Backtesting Engine.

    Pipeline

    Raw Data
        ↓
    IndicatorEngine
        ↓
    Feature Pipeline
        ↓
    Decision Engine
        ↓
    Risk Manager
        ↓
    Paper Broker
    """

    def __init__(
        self,
        strategy: BaseStrategy | None = None,
    ):

        self.portfolio = Portfolio(
            settings.starting_balance
        )

        self.broker = PaperBroker(
            self.portfolio
        )

        self.risk_manager = RiskManager()

        self.decision_engine = DecisionEngine(
            strategy=strategy,
        )

    def run(
        self,
        df,
    ):

        # --------------------------------------------------
        # Build indicators + AI features
        # --------------------------------------------------

        df = IndicatorEngine.calculate_all(df)

        current_trade = None

        for i in range(
            settings.warmup_candles,
            len(df) - 1,
        ):

            history = df.iloc[: i + 1]

            decision = self.decision_engine.evaluate(
                history
            )

            signal = decision.signal

            execution = df.iloc[i + 1]

            entry_price = execution["open"]

            current_price = execution["close"]

            current_high = execution["high"]

            current_low = execution["low"]

            atr = history.iloc[-1]["atr"]

            entry_time = str(
                execution["timestamp"]
            )

            logger.info(
                f"{entry_time} | "
                f"RAW={decision.raw_signal} | "
                f"FINAL={decision.signal} | "
                f"SCORE={decision.score}"
            )

            # --------------------------------------------------
            # Manage existing trade
            # --------------------------------------------------

            if current_trade is not None:

                PositionManager.update(
                    trade=current_trade,
                    current_price=current_price,
                    atr=atr,
                )

                if current_low <= current_trade.stop_loss:

                    current_trade.close(
                        exit_price=current_trade.stop_loss,
                        exit_time=entry_time,
                        reason="STOP_LOSS",
                    )

                    self.broker.close(
                        current_trade
                    )

                    logger.info(
                        f"STOP LOSS @ {current_trade.stop_loss:.2f}"
                    )

                    current_trade = None

                    continue

                if current_high >= current_trade.take_profit:

                    current_trade.close(
                        exit_price=current_trade.take_profit,
                        exit_time=entry_time,
                        reason="TAKE_PROFIT",
                    )

                    self.broker.close(
                        current_trade
                    )

                    logger.info(
                        f"TAKE PROFIT @ {current_trade.take_profit:.2f}"
                    )

                    current_trade = None

                    continue

            # --------------------------------------------------
            # BUY
            # --------------------------------------------------

            if (
                signal == Signal.BUY
                and current_trade is None
                and PortfolioRiskManager.can_open_position(
                    self.portfolio
                )
            ):

                risk_amount = self.risk_manager.risk_amount(
                    self.portfolio.balance
                )

                if not PortfolioRiskManager.can_take_risk(
                    self.portfolio,
                    risk_amount,
                ):
                    continue

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
                    symbol=settings.symbols[0],
                    side=OrderSide.BUY,
                    entry_price=entry_price,
                    quantity=quantity,
                    entry_time=entry_time,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_amount=risk_amount,
                )

                logger.info(
                    f"BUY OPENED @ {entry_price:.2f}"
                )

                self.broker.buy(
                    current_trade
                )

            # --------------------------------------------------
            # SELL
            # --------------------------------------------------

            elif (
                signal == Signal.SELL
                and current_trade is not None
            ):

                current_trade.close(
                    exit_price=entry_price,
                    exit_time=entry_time,
                    reason="SIGNAL",
                )

                self.broker.close(
                    current_trade
                )

                logger.info(
                    f"SELL @ {entry_price:.2f}"
                )

                current_trade = None

        return self.portfolio