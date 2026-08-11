from app.analytics.learning_engine import LearningEngine

from app.backtesting.portfolio import Portfolio
from app.backtesting.trade import Trade

from app.broker.paper_broker import PaperBroker

from app.config.settings import settings

from app.core.enums import OrderSide
from app.core.enums import Signal

from app.data.validator import DataValidator

from app.decision.decision_engine import DecisionEngine

from app.indicators.indicator_engine import IndicatorEngine

from app.logging.logger import logger

from app.portfolio.portfolio_manager import PortfolioManager

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

        self.portfolio_manager = PortfolioManager()

        self.broker = PaperBroker(
            self.portfolio,
            fee_rate=settings.commission,
            slippage=settings.slippage,
        )

        self.risk_manager = RiskManager()

        self.decision_engine = DecisionEngine(
            strategy=strategy,
        )

    @staticmethod
    def _register_learning(trade: Trade) -> None:
        """
        Credits a closed trade's outcome back to LearningEngine, but
        only for the strategies that contributed to the winning side
        of the vote that opened it (Trade.contributing_strategies is
        only non-empty when voting produced this trade - see
        DecisionEngine._vote). Losing-side voters are not penalized
        for a trade whose direction they didn't pick.
        """

        for strategy_name in trade.contributing_strategies:

            LearningEngine.register_trade(
                strategy_name,
                trade.profit,
            )

    def run(
        self,
        data,
    ):
        """
        - data: a single symbol's DataFrame -> classic single-symbol
          backtest against settings.symbols[0] (unchanged behavior).
        - data: dict[symbol, DataFrame] -> multi-position backtest
          across all given symbols, sharing this Backtester's balance
          and risk limits. Requires settings.enable_multi_position=True
          (raises otherwise) - this is a deliberate opt-in safety rail,
          not a capability check.
        """

        if isinstance(data, dict):
            return self._run_multi(data)

        return self._run_single(data)

    def _run_single(self, df):

        # --------------------------------------------------
        # Build indicators + AI features
        # --------------------------------------------------

        df = IndicatorEngine.calculate_all(df)

        symbol = settings.symbols[0]

        for i in range(
            settings.warmup_candles,
            len(df) - 1,
        ):

            self._step(
                symbol,
                history=df.iloc[: i + 1],
                execution=df.iloc[i + 1],
            )

        return self.portfolio

    def _run_multi(self, market_data: dict):

        if not settings.enable_multi_position:

            raise ValueError(
                "Backtester.run() received multiple symbols but "
                "settings.enable_multi_position is False. Enable it "
                "explicitly to run a multi-position backtest."
            )

        prepared = {}

        for symbol, df in market_data.items():

            # Validate the RAW candles first, same as main.py's
            # single-symbol flow - IndicatorEngine.calculate_all()
            # introduces NaN warmup rows that would always fail
            # DataValidator's NaN check if validated afterward.
            if not DataValidator.validate(df):

                logger.warning(
                    f"{symbol}: invalid market data, skipping in "
                    "multi-position backtest"
                )

                continue

            prepared[symbol] = IndicatorEngine.calculate_all(df)

        if not prepared:

            logger.warning(
                "No valid symbols remaining for multi-position backtest"
            )

            return self.portfolio

        aligned = self._align_timestamps(prepared)

        length = min(len(df) for df in aligned.values())

        for i in range(
            settings.warmup_candles,
            length - 1,
        ):

            for symbol, df in aligned.items():

                self._step(
                    symbol,
                    history=df.iloc[: i + 1],
                    execution=df.iloc[i + 1],
                )

        return self.portfolio

    @staticmethod
    def _align_timestamps(market_data: dict) -> dict:
        """
        Restricts every symbol's dataframe to the intersection of their
        timestamps, so the shared candle-by-candle loop always compares
        the same wall-clock bar across symbols. Indicators are computed
        on each symbol's full, unaligned series beforehand (by
        _run_multi) so warmup stays correct even though this can still
        leave internal gaps for a symbol that lost middle candles here.
        Every symbol's drop count is logged - never silent.
        """

        common = None

        for df in market_data.values():

            timestamps = set(df["timestamp"])

            common = (
                timestamps
                if common is None
                else common & timestamps
            )

        aligned = {}

        for symbol, df in market_data.items():

            aligned_df = (
                df[df["timestamp"].isin(common)]
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            dropped = len(df) - len(aligned_df)

            if dropped > 0:

                logger.warning(
                    f"{symbol}: {dropped} candles dropped outside the "
                    "timestamp intersection (multi-symbol alignment)"
                )

            aligned[symbol] = aligned_df

        return aligned

    def _step(
        self,
        symbol: str,
        history,
        execution,
    ) -> None:
        """
        Evaluates and acts on a single symbol's single candle step -
        the shared body for both single- and multi-position runs.
        """

        decision = self.decision_engine.evaluate(
            history
        )

        signal = decision.signal

        entry_price = execution["open"]

        current_price = execution["close"]

        current_high = execution["high"]

        current_low = execution["low"]

        atr = history.iloc[-1]["atr"]

        entry_time = str(
            execution["timestamp"]
        )

        logger.info(
            f"{symbol} | {entry_time} | "
            f"RAW={decision.raw_signal} | "
            f"FINAL={decision.signal} | "
            f"SCORE={decision.score}"
        )

        current_trade = self.portfolio_manager.get_position(
            symbol
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

                self.portfolio_manager.close_trade(
                    current_trade
                )

                self._register_learning(current_trade)

                logger.info(
                    f"{symbol} | STOP LOSS @ {current_trade.stop_loss:.2f}"
                )

                return

            if current_high >= current_trade.take_profit:

                current_trade.close(
                    exit_price=current_trade.take_profit,
                    exit_time=entry_time,
                    reason="TAKE_PROFIT",
                )

                self.broker.close(
                    current_trade
                )

                self.portfolio_manager.close_trade(
                    current_trade
                )

                self._register_learning(current_trade)

                logger.info(
                    f"{symbol} | TAKE PROFIT @ {current_trade.take_profit:.2f}"
                )

                return

        # --------------------------------------------------
        # BUY
        # --------------------------------------------------

        if (
            signal == Signal.BUY
            and self.portfolio_manager.can_open_trade(symbol)
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
                return

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

            new_trade = Trade(
                symbol=symbol,
                side=OrderSide.BUY,
                entry_price=entry_price,
                quantity=quantity,
                entry_time=entry_time,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_amount=risk_amount,
                contributing_strategies=decision.contributing_strategies,
            )

            logger.info(
                f"{symbol} | BUY OPENED @ {entry_price:.2f}"
            )

            self.broker.buy(
                new_trade
            )

            self.portfolio_manager.register_trade(
                new_trade
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

            self.portfolio_manager.close_trade(
                current_trade
            )

            self._register_learning(current_trade)

            logger.info(
                f"{symbol} | SELL @ {entry_price:.2f}"
            )