import pandas as pd

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

        # Every surviving symbol must share the same candle period.
        # This can only happen via a programmatic Backtester().run(dict)
        # call with mismatched timeframes - settings.timeframe is a
        # single scalar and MultiDataProvider.fetch_all() applies it to
        # every symbol, so --multi-position can never produce this. A
        # mixed-timeframe intersection is still a valid arithmetic
        # progression (e.g. 1h x 2h -> a clean 2h grid), so it would
        # pass the gap check below undetected - it has to be caught
        # here, before alignment, as the caller error it is.
        periods = {
            symbol: self._modal_delta(df["timestamp"])
            for symbol, df in prepared.items()
        }

        if len(set(periods.values())) > 1:

            details = ", ".join(
                f"{symbol}={period}"
                for symbol, period in periods.items()
            )

            raise ValueError(
                "Backtester.run() received symbols on different candle "
                "timeframes, which multi-position backtesting does not "
                f"support (each symbol's dominant candle interval: "
                f"{details}). Fetch every symbol on the same timeframe "
                "before calling run()."
            )

        aligned = self._align_timestamps(prepared)

        # Defensive only: _align_timestamps always returns one entry per
        # input symbol (rows may be empty, but the dict itself is not),
        # and `prepared` is already guaranteed non-empty above. Guards
        # against min() raising on an empty sequence if that invariant
        # is ever broken by a future refactor.
        if not aligned:

            logger.warning(
                "Timestamp alignment produced no symbols; "
                "multi-position backtest did not run"
            )

            return self.portfolio

        length = min(len(df) for df in aligned.values())

        if length <= settings.warmup_candles + 1:

            if length == 0:

                logger.warning(
                    "Symbols share no common timestamps after alignment "
                    f"({', '.join(aligned.keys())}); multi-position "
                    "backtest did not run"
                )

            else:

                logger.warning(
                    f"Timestamp intersection has only {length} candles, "
                    "which yields zero backtest steps (need more than "
                    f"warmup_candles + 1 = {settings.warmup_candles + 1}); "
                    "multi-position backtest did not run"
                )

            return self.portfolio

        # All aligned frames share identical timestamps by construction
        # (_align_timestamps filters every symbol down to the same
        # intersection), so checking any one of them checks the shared
        # axis. A gap here can only originate from an input symbol whose
        # own series was not evenly spaced to begin with - see
        # _describe_alignment_gap's docstring for why this stops the
        # whole run instead of dropping a symbol like the invalid-data
        # path above does.
        common_timestamps = next(iter(aligned.values()))["timestamp"]

        if not DataValidator._timestamps_are_evenly_spaced(common_timestamps):

            raise ValueError(
                self._describe_alignment_gap(prepared, common_timestamps)
            )

        if length < DataValidator.MINIMUM_ROWS:

            logger.warning(
                f"Timestamp intersection has only {length} candles "
                f"(below DataValidator.MINIMUM_ROWS={DataValidator.MINIMUM_ROWS}); "
                f"multi-position backtest will run but only "
                f"{length - settings.warmup_candles - 1} step(s), which "
                "may not be statistically meaningful"
            )

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
    def _modal_delta(timestamps) -> pd.Timedelta:
        """
        The most common gap between consecutive timestamps in a sorted
        series - used as "the" candle period for a symbol. Unlike the
        median (which DataValidator's gap check uses), the mode is what
        _describe_alignment_gap needs to build an expected time grid:
        the period real candles actually sit on.
        """

        deltas = (
            timestamps
            .sort_values()
            .diff()
            .dropna()
        )

        if deltas.empty:
            return pd.Timedelta(0)

        return deltas.mode().iloc[0]

    @staticmethod
    def _describe_alignment_gap(
        prepared: dict,
        common_timestamps,
    ) -> str:
        """
        Builds a diagnostic ValueError message for a gap discovered in
        the post-alignment shared timestamp axis (see _run_multi).

        Why this raises instead of dropping the offending symbol (unlike
        the invalid-raw-data path earlier in _run_multi, which skips and
        continues): _align_timestamps restricts every symbol to the
        SAME intersection, so after alignment every symbol's timestamps
        are byte-for-byte identical - there is no such thing as "the
        gapped symbol" at this point, only a gapped shared axis. Dropping
        one arbitrarily chosen symbol would not fix anything (the axis
        is shared), and dropping all of them defeats the purpose of a
        multi-symbol run. So this stops the whole run instead, with
        enough detail (from `prepared`, the pre-alignment per-symbol
        data) to name which original symbol(s) are actually missing the
        candle and let the caller fix the input.
        """

        expected_period = Backtester._modal_delta(common_timestamps)

        common_set = set(common_timestamps)

        start, end = min(common_set), max(common_set)

        expected_grid = pd.date_range(
            start,
            end,
            freq=expected_period,
        )

        missing = sorted(set(expected_grid) - common_set)

        gap_descriptions = []

        for timestamp in missing:

            missing_from = [
                symbol
                for symbol, df in prepared.items()
                if timestamp not in set(df["timestamp"])
            ]

            gap_descriptions.append(
                f"{timestamp} missing (expected every {expected_period}); "
                f"not present in: {', '.join(missing_from) or 'unknown'}"
            )

        return (
            "Backtester._run_multi(): the aligned timestamp axis has "
            f"{len(missing)} gap(s), which multi-position backtesting "
            "cannot proceed through safely (crossover-style strategies "
            "compare adjacent rows and would misread a gap as a real "
            "adjacent candle). "
            + "; ".join(gap_descriptions)
            + ". Fix by excluding the symbol(s) named above from this "
            "run, or narrowing the date range to a window where all "
            "symbols have complete data."
        )

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