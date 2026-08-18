"""
Covers app.arbitrage.funding_trader.FundingArbitrageTrader:

- observe-only vs enabled-and-opens, gated by
  settings.enable_funding_arbitrage (mirrors LiveTrader's
  enable_live_paper_trading split).
- the entry sanity check (refuses to open into negative funding or an
  abnormally wide basis).
- managing an already-open position: funding settlement recording, the
  liquidation-warning auto-close, and the negative-funding-streak
  circuit breaker - both routed through the injected executor's
  close_position(), never bypassing it.
- run_forever()'s per-iteration resilience: transient errors are
  retried, UnbalancedPositionError/ArbitrageStateCorruptError are
  never treated as transient.
- state persistence/restoration across a simulated restart.

poll_once() is exercised directly in most tests via fake data-provider/
executor doubles - no real network access, sleeping, or ccxt calls.
"""

import pandas as pd
import pytest

from app.arbitrage.arbitrage_state_store import (
    ArbitrageStateCorruptError,
    ArbitrageStateStore,
)
from app.arbitrage.arbitrage_status_store import ArbitrageStatusStore
from app.arbitrage.execution import UnbalancedPositionError
from app.arbitrage.funding_trader import FundingArbitrageTrader
from app.arbitrage.position import ArbitragePosition, compute_liquidation_price
from app.config.settings import settings


@pytest.fixture(autouse=True)
def _isolate_arbitrage_stores(tmp_path, monkeypatch):

    monkeypatch.setattr(
        ArbitrageStateStore, "FILE", tmp_path / "arbitrage_state.json",
    )
    monkeypatch.setattr(
        ArbitrageStatusStore, "FILE", tmp_path / "arbitrage_status.json",
    )


class FakeSpotProvider:

    def __init__(self, price=60000.0):

        self.price = price
        self.calls = 0

    def fetch_ticker(self, symbol):

        self.calls += 1

        return self.price


class FakeFundingDataProvider:

    def __init__(self, funding_rate=0.0001, spot_price=60000.0, perp_price=60005.0):

        self.spot = FakeSpotProvider(spot_price)

        self.funding_rate = funding_rate
        self.perp_price = perp_price

        self.funding_calls = 0
        self.perp_ticker_calls = 0

    def fetch_funding_rate(self, symbol):

        self.funding_calls += 1

        return self.funding_rate

    def fetch_perp_ticker(self, symbol):

        self.perp_ticker_calls += 1

        return self.perp_price


class FakeExecutor:
    """
    open_result/close_result: set to an ArbitragePosition to have the
    call succeed and return it, or to an Exception INSTANCE to have
    the call raise it.
    """

    def __init__(self):

        self.open_calls = []
        self.close_calls = []
        self.open_result = None
        self.close_result = None

    def open_position(self, symbol, notional, leverage, maintenance_margin_rate, timestamp):

        self.open_calls.append(
            dict(
                symbol=symbol,
                notional=notional,
                leverage=leverage,
                maintenance_margin_rate=maintenance_margin_rate,
                timestamp=timestamp,
            )
        )

        if isinstance(self.open_result, Exception):
            raise self.open_result

        return self.open_result

    def close_position(self, position, timestamp):

        self.close_calls.append(dict(position=position, timestamp=timestamp))

        if isinstance(self.close_result, Exception):
            raise self.close_result

        position.status = "CLOSED"
        position.exit_time = timestamp

        return position


def _open_position(leverage=5, mmr=0.004, spot_qty=0.1, entry_price=60000.0):

    return ArbitragePosition(
        symbol="BTC/USDT",
        leverage=leverage,
        maintenance_margin_rate=mmr,
        entry_time="2026-01-01T00:00:00",
        spot_entry_price=entry_price,
        spot_qty=spot_qty,
        perp_entry_price=entry_price,
        perp_qty=spot_qty,
        margin=entry_price * spot_qty / leverage,
        status="OPEN",
    )


def _trader(provider=None, executor=None, symbol="BTC/USDT"):

    return FundingArbitrageTrader(
        symbol,
        data_provider=provider or FakeFundingDataProvider(),
        executor=executor or FakeExecutor(),
    )


# ----------------------------------------------------------------
# construction / defaults
# ----------------------------------------------------------------


def test_defaults_symbol_from_settings(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_symbol", "ETH/USDT")

    trader = FundingArbitrageTrader(
        data_provider=FakeFundingDataProvider(), executor=FakeExecutor(),
    )

    assert trader.symbol == "ETH/USDT"
    assert trader.perp_symbol == "ETH/USDT:USDT"


def test_starts_flat_with_no_prior_state():

    trader = _trader()

    assert trader.position is None
    assert trader.closed_positions == []


# ----------------------------------------------------------------
# observe-only vs enabled
# ----------------------------------------------------------------


def test_stays_flat_when_disabled(monkeypatch):

    monkeypatch.setattr(settings, "enable_funding_arbitrage", False)

    executor = FakeExecutor()
    trader = _trader(executor=executor)

    trader.poll_once()

    assert trader.position is None
    assert executor.open_calls == []


def test_opens_when_enabled_and_conditions_are_favorable(monkeypatch):

    monkeypatch.setattr(settings, "enable_funding_arbitrage", True)
    monkeypatch.setattr(settings, "starting_balance", 10000.0)
    monkeypatch.setattr(settings, "funding_arb_leverage", 1)

    provider = FakeFundingDataProvider(
        funding_rate=0.0001, spot_price=60000.0, perp_price=60005.0,
    )
    executor = FakeExecutor()
    executor.open_result = _open_position()

    trader = _trader(provider=provider, executor=executor)
    trader.poll_once()

    assert trader.position is executor.open_result
    assert len(executor.open_calls) == 1
    # deployable notional at leverage=1 on 10000 capital = 5000
    assert executor.open_calls[0]["notional"] == pytest.approx(5000.0)
    assert executor.open_calls[0]["leverage"] == 1


def test_does_not_open_when_funding_is_currently_negative(monkeypatch):

    monkeypatch.setattr(settings, "enable_funding_arbitrage", True)

    provider = FakeFundingDataProvider(funding_rate=-0.0001)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.poll_once()

    assert trader.position is None
    assert executor.open_calls == []


def test_does_not_open_when_basis_is_too_wide(monkeypatch):

    monkeypatch.setattr(settings, "enable_funding_arbitrage", True)

    # basis = (61000-60000)/60000 = 1.67%, far above the 0.5% sanity
    # threshold.
    provider = FakeFundingDataProvider(
        funding_rate=0.0001, spot_price=60000.0, perp_price=61000.0,
    )
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.poll_once()

    assert trader.position is None
    assert executor.open_calls == []


def test_does_not_open_a_second_position_while_one_is_open(monkeypatch):

    monkeypatch.setattr(settings, "enable_funding_arbitrage", True)

    executor = FakeExecutor()
    trader = _trader(executor=executor)
    trader.position = _open_position()

    trader.poll_once()

    assert executor.open_calls == []


# ----------------------------------------------------------------
# managing an open position - funding settlement
# ----------------------------------------------------------------


def test_records_funding_payment_against_the_open_position():

    provider = FakeFundingDataProvider(funding_rate=0.0002, perp_price=60000.0)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.position = _open_position(spot_qty=1.0, entry_price=60000.0)

    trader.poll_once()

    assert len(trader.position.funding_events) == 1
    assert trader.position.cumulative_funding == pytest.approx(
        1.0 * 60000.0 * 0.0002
    )


def test_state_is_saved_after_every_poll(tmp_path):

    provider = FakeFundingDataProvider(funding_rate=0.0001)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.position = _open_position()

    trader.poll_once()

    assert ArbitrageStateStore.FILE.exists()

    position, closed = ArbitrageStateStore.restore()

    assert position is not None
    assert position.cumulative_funding == pytest.approx(
        trader.position.cumulative_funding
    )


# ----------------------------------------------------------------
# liquidation-warning auto-close - routed through executor.close_position
# ----------------------------------------------------------------


def test_force_closes_via_executor_when_liquidation_warning_trips(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_liquidation_warning_pct", 0.5)

    leverage = 5
    mmr = 0.004
    entry_price = 60000.0

    liquidation_price = compute_liquidation_price(entry_price, leverage, mmr)

    # at (or above) the liquidation price, margin_ratio is ~1.0, well
    # past the 0.5 warning threshold.
    provider = FakeFundingDataProvider(
        funding_rate=0.0001, perp_price=liquidation_price,
    )
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.position = _open_position(leverage=leverage, mmr=mmr, entry_price=entry_price)
    original_position = trader.position

    trader.poll_once()

    assert len(executor.close_calls) == 1
    assert executor.close_calls[0]["position"] is original_position
    assert trader.position is None
    assert trader.closed_positions == [original_position]
    assert original_position.status == "CLOSED"


def test_does_not_close_when_margin_ratio_is_far_from_warning(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_liquidation_warning_pct", 0.5)

    provider = FakeFundingDataProvider(funding_rate=0.0001, perp_price=60050.0)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    trader.position = _open_position(leverage=5, mmr=0.004, entry_price=60000.0)

    trader.poll_once()

    assert executor.close_calls == []
    assert trader.position is not None


# ----------------------------------------------------------------
# negative-funding-streak circuit breaker - also routed through
# executor.close_position
# ----------------------------------------------------------------


def test_force_closes_when_negative_streak_reaches_the_breaker(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_max_negative_streak", 3)

    provider = FakeFundingDataProvider(funding_rate=-0.0001, perp_price=60000.0)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    position = _open_position(entry_price=60000.0)
    # two prior negative settlements already recorded - this poll's
    # negative rate will be the third, tripping the breaker.
    position.funding_events = [
        {"timestamp": "t1", "funding_rate": -0.0001, "mark_price": 60000.0, "payment": -0.6},
        {"timestamp": "t2", "funding_rate": -0.0001, "mark_price": 60000.0, "payment": -0.6},
    ]
    trader.position = position

    trader.poll_once()

    assert len(executor.close_calls) == 1
    assert trader.position is None
    assert trader.closed_positions[0].status == "CLOSED"


def test_does_not_close_when_streak_is_below_the_breaker(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_max_negative_streak", 5)

    provider = FakeFundingDataProvider(funding_rate=-0.0001, perp_price=60000.0)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    position = _open_position(entry_price=60000.0)
    position.funding_events = [
        {"timestamp": "t1", "funding_rate": -0.0001, "mark_price": 60000.0, "payment": -0.6},
    ]
    trader.position = position

    trader.poll_once()

    assert executor.close_calls == []
    assert trader.position is not None


def test_a_positive_settlement_resets_the_streak_before_the_breaker_check(monkeypatch):

    monkeypatch.setattr(settings, "funding_arb_max_negative_streak", 2)

    provider = FakeFundingDataProvider(funding_rate=0.0001, perp_price=60000.0)
    executor = FakeExecutor()

    trader = _trader(provider=provider, executor=executor)
    position = _open_position(entry_price=60000.0)
    position.funding_events = [
        {"timestamp": "t1", "funding_rate": -0.0001, "mark_price": 60000.0, "payment": -0.6},
    ]
    trader.position = position

    # this poll's rate is POSITIVE, so after recording it the trailing
    # streak is 0, not 2 - must not close.
    trader.poll_once()

    assert executor.close_calls == []
    assert trader.position is not None


# ----------------------------------------------------------------
# run_forever resilience
# ----------------------------------------------------------------


def test_run_forever_retries_a_transient_error_and_increments_error_count(monkeypatch):

    monkeypatch.setattr(settings, "live_error_retry_seconds", 0)

    trader = _trader()
    monkeypatch.setattr(trader, "_wait_for_next_funding", lambda: None)

    calls = {"count": 0}

    def fake_poll_once():

        calls["count"] += 1

        if calls["count"] == 1:
            raise RuntimeError("simulated transient failure")

        raise KeyboardInterrupt

    monkeypatch.setattr(trader, "poll_once", fake_poll_once)

    with pytest.raises(KeyboardInterrupt):
        trader.run_forever()

    assert trader._error_count == 1
    assert trader._last_error == "simulated transient failure"


def test_run_forever_stops_immediately_on_unbalanced_position_error(monkeypatch):

    trader = _trader()
    monkeypatch.setattr(trader, "_wait_for_next_funding", lambda: None)

    def fake_poll_once():
        raise UnbalancedPositionError("simulated desync")

    monkeypatch.setattr(trader, "poll_once", fake_poll_once)

    with pytest.raises(UnbalancedPositionError):
        trader.run_forever()

    # never counted as a routine/transient error.
    assert trader._error_count == 0


def test_run_forever_stops_immediately_on_corrupt_state_error(monkeypatch):

    trader = _trader()
    monkeypatch.setattr(trader, "_wait_for_next_funding", lambda: None)

    def fake_poll_once():
        raise ArbitrageStateCorruptError("simulated corruption")

    monkeypatch.setattr(trader, "poll_once", fake_poll_once)

    with pytest.raises(ArbitrageStateCorruptError):
        trader.run_forever()

    assert trader._error_count == 0


def test_run_forever_writes_a_status_heartbeat_before_each_wait(monkeypatch):

    trader = _trader()
    monkeypatch.setattr(trader, "_wait_for_next_funding", lambda: None)

    calls = {"count": 0}

    def fake_poll_once():

        calls["count"] += 1

        if calls["count"] >= 2:
            raise KeyboardInterrupt

        return None

    monkeypatch.setattr(trader, "poll_once", fake_poll_once)

    with pytest.raises(KeyboardInterrupt):
        trader.run_forever()

    status = ArbitrageStatusStore.load()

    assert status is not None
    assert status["symbol"] == "BTC/USDT"
    assert status["poll_count"] == 1


# ----------------------------------------------------------------
# state persistence across a simulated restart
# ----------------------------------------------------------------


def test_state_restored_on_a_fresh_trader_instance():

    provider = FakeFundingDataProvider(funding_rate=0.0001)
    executor = FakeExecutor()

    first = _trader(provider=provider, executor=executor)
    first.position = _open_position(entry_price=60000.0)
    first.poll_once()

    expected_cumulative = first.position.cumulative_funding

    second = FundingArbitrageTrader(
        "BTC/USDT",
        data_provider=FakeFundingDataProvider(),
        executor=FakeExecutor(),
    )

    assert second.position is not None
    assert second.position.cumulative_funding == pytest.approx(expected_cumulative)


def test_restart_count_increments_across_instances():

    first = _trader()

    assert first._restart_count == 0

    first._save_status_heartbeat()

    second = FundingArbitrageTrader(
        "BTC/USDT",
        data_provider=FakeFundingDataProvider(),
        executor=FakeExecutor(),
    )

    assert second._restart_count == 1


def test_corrupt_arbitrage_state_file_prevents_construction(tmp_path, monkeypatch):

    monkeypatch.setattr(
        ArbitrageStateStore, "FILE", tmp_path / "arbitrage_state.json",
    )

    ArbitrageStateStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStateStore.FILE.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ArbitrageStateCorruptError):
        FundingArbitrageTrader(
            "BTC/USDT",
            data_provider=FakeFundingDataProvider(),
            executor=FakeExecutor(),
        )


def test_corrupt_arbitrage_status_file_resets_restart_count_instead_of_raising(
    tmp_path, monkeypatch,
):

    monkeypatch.setattr(
        ArbitrageStatusStore, "FILE", tmp_path / "arbitrage_status.json",
    )

    ArbitrageStatusStore.FILE.parent.mkdir(exist_ok=True)
    ArbitrageStatusStore.FILE.write_text("{not valid json", encoding="utf-8")

    trader = FundingArbitrageTrader(
        "BTC/USDT",
        data_provider=FakeFundingDataProvider(),
        executor=FakeExecutor(),
    )

    assert trader._restart_count == 0


# ----------------------------------------------------------------
# funding-interval timing (pure calculation, no sleeping)
# ----------------------------------------------------------------


def test_seconds_until_next_funding_at_exact_boundary():

    trader = _trader()

    now = pd.Timestamp("2026-01-01T00:00:00")

    assert trader.seconds_until_next_funding(now) == pytest.approx(8 * 3600)


def test_seconds_until_next_funding_partway_through_a_window():

    trader = _trader()

    now = pd.Timestamp("2026-01-01T04:00:00")

    assert trader.seconds_until_next_funding(now) == pytest.approx(4 * 3600)


def test_seconds_until_next_funding_just_before_a_boundary():

    trader = _trader()

    now = pd.Timestamp("2026-01-01T15:59:00")

    assert trader.seconds_until_next_funding(now) == pytest.approx(60)
