import pytest

from app.arbitrage.execution import (
    ArbitrageExecutor,
    UnbalancedPositionError,
    to_perpetual_symbol,
)
from app.arbitrage.position import ArbitragePosition
from app.data.exceptions import DataProviderError


class FakeSpotProvider:
    """
    fail_on_call, if set, raises DataProviderError on that specific
    1-indexed call number (so a test can make the FIRST fetch_ticker
    call - opening the spot leg - succeed while a SECOND call - the
    unwind attempt - fails, or vice versa).
    """

    def __init__(self, price=60000.0, fail_on_call=None):

        self.price = price
        self.fail_on_call = fail_on_call
        self.calls = 0

    def fetch_ticker(self, symbol):

        self.calls += 1

        if self.fail_on_call == self.calls:
            raise DataProviderError(
                f"simulated spot ticker failure on call {self.calls}"
            )

        return self.price


class FakeDataProvider:

    def __init__(
        self,
        spot_price=60000.0,
        perp_price=60010.0,
        spot_fail_on_call=None,
        perp_fail_on_call=None,
    ):

        self.spot = FakeSpotProvider(spot_price, fail_on_call=spot_fail_on_call)

        self.perp_price = perp_price
        self.perp_fail_on_call = perp_fail_on_call
        self.perp_calls = 0

    def fetch_perp_ticker(self, symbol):

        self.perp_calls += 1

        if self.perp_fail_on_call == self.perp_calls:
            raise DataProviderError(
                f"simulated perp ticker failure on call {self.perp_calls}"
            )

        return self.perp_price


def _executor(data_provider, spot_fee=0.001, futures_fee=0.0005, slippage=0.0005):

    return ArbitrageExecutor(
        data_provider=data_provider,
        spot_fee_rate=spot_fee,
        futures_fee_rate=futures_fee,
        slippage_rate=slippage,
    )


def _open_position(symbol="BTC/USDT", leverage=1, mmr=0.004, spot_qty=1.0, perp_qty=None):

    perp_qty = spot_qty if perp_qty is None else perp_qty

    return ArbitragePosition(
        symbol=symbol,
        leverage=leverage,
        maintenance_margin_rate=mmr,
        entry_time="2026-01-01T00:00:00",
        spot_entry_price=60000.0,
        spot_qty=spot_qty,
        perp_entry_price=60010.0,
        perp_qty=perp_qty,
        margin=60000.0 * spot_qty / leverage,
        status="OPEN",
    )


# ----------------------------------------------------------------
# to_perpetual_symbol
# ----------------------------------------------------------------


def test_to_perpetual_symbol():

    assert to_perpetual_symbol("BTC/USDT") == "BTC/USDT:USDT"
    assert to_perpetual_symbol("ETH/USDT") == "ETH/USDT:USDT"


# ----------------------------------------------------------------
# open_position - happy path
# ----------------------------------------------------------------


def test_open_position_happy_path_fills_both_legs_delta_neutral():

    provider = FakeDataProvider(spot_price=60000.0, perp_price=60010.0)
    executor = _executor(provider)

    position = executor.open_position(
        "BTC/USDT",
        notional=6000.0,
        leverage=1,
        maintenance_margin_rate=0.004,
        timestamp="2026-01-01T00:00:00",
    )

    assert position.status == "OPEN"

    # both legs share the SAME base-asset quantity (true delta
    # neutrality) rather than independently re-deriving quantity from
    # notional at each leg's own (slightly different) price.
    assert position.spot_qty == position.perp_qty

    # spot BUY slippage pushes the fill price above market.
    assert position.spot_entry_price > 60000.0
    # perp OPEN-SHORT (selling the contract) slippage pushes the fill
    # price below market.
    assert position.perp_entry_price < 60010.0

    assert provider.spot.calls == 1
    assert provider.perp_calls == 1


def test_open_position_quantity_matches_notional_after_slippage():

    provider = FakeDataProvider(spot_price=60000.0)
    executor = _executor(provider, slippage=0.0005)

    position = executor.open_position(
        "BTC/USDT", notional=6000.0, leverage=1,
        maintenance_margin_rate=0.004, timestamp="t",
    )

    expected_execution_price = 60000.0 * 1.0005
    expected_qty = 6000.0 / expected_execution_price

    assert position.spot_qty == pytest.approx(expected_qty)


def test_open_position_margin_reflects_leverage():

    provider = FakeDataProvider(spot_price=60000.0, perp_price=60000.0)
    executor = _executor(provider, slippage=0.0)  # isolate leverage effect from slippage

    position = executor.open_position(
        "BTC/USDT", notional=6000.0, leverage=5,
        maintenance_margin_rate=0.004, timestamp="t",
    )

    expected_margin = position.perp_entry_price * position.perp_qty / 5

    assert position.margin == pytest.approx(expected_margin)


# ----------------------------------------------------------------
# open_position - perp leg fails, spot leg is unwound
# ----------------------------------------------------------------


def test_open_position_perp_leg_failure_unwinds_spot_leg_and_reraises():

    # spot succeeds on BOTH calls: the initial open buy AND the
    # unwind sell. perp fails on its only call.
    provider = FakeDataProvider(perp_fail_on_call=1)
    executor = _executor(provider)

    with pytest.raises(DataProviderError):

        executor.open_position(
            "BTC/USDT", notional=6000.0, leverage=1,
            maintenance_margin_rate=0.004, timestamp="t",
        )

    # spot leg was bought once, then sold back once - never left open.
    assert provider.spot.calls == 2
    assert provider.perp_calls == 1


def test_open_position_perp_leg_failure_never_returns_a_position():
    """
    The failure path must never produce an ArbitragePosition at all -
    there is no code path where the caller could mistake this for a
    (partially) successful open.
    """

    provider = FakeDataProvider(perp_fail_on_call=1)
    executor = _executor(provider)

    result = None

    try:
        result = executor.open_position(
            "BTC/USDT", notional=6000.0, leverage=1,
            maintenance_margin_rate=0.004, timestamp="t",
        )
    except DataProviderError:
        pass

    assert result is None


# ----------------------------------------------------------------
# open_position - perp leg fails AND the unwind also fails
# ----------------------------------------------------------------


def test_open_position_unwind_failure_raises_unbalanced_position_error():

    # spot succeeds on call #1 (the open buy) but fails on call #2
    # (the unwind attempt).
    provider = FakeDataProvider(spot_fail_on_call=2, perp_fail_on_call=1)
    executor = _executor(provider)

    with pytest.raises(UnbalancedPositionError):

        executor.open_position(
            "BTC/USDT", notional=6000.0, leverage=1,
            maintenance_margin_rate=0.004, timestamp="t",
        )

    assert provider.spot.calls == 2
    assert provider.perp_calls == 1


def test_open_position_unwind_failure_error_names_both_underlying_causes():

    provider = FakeDataProvider(spot_fail_on_call=2, perp_fail_on_call=1)
    executor = _executor(provider)

    with pytest.raises(UnbalancedPositionError) as excinfo:

        executor.open_position(
            "BTC/USDT", notional=6000.0, leverage=1,
            maintenance_margin_rate=0.004, timestamp="t",
        )

    message = str(excinfo.value)

    assert "perp" in message.lower()
    assert "unwind" in message.lower() or "spot" in message.lower()


# ----------------------------------------------------------------
# close_position - happy path
# ----------------------------------------------------------------


def test_close_position_happy_path_closes_both_legs():

    provider = FakeDataProvider(spot_price=61000.0, perp_price=61010.0)
    executor = _executor(provider)

    position = _open_position()

    closed = executor.close_position(position, timestamp="2026-01-02T00:00:00")

    assert closed is position
    assert closed.status == "CLOSED"
    assert closed.exit_time == "2026-01-02T00:00:00"

    # closing a short = buying back -> price pushed ABOVE market.
    assert closed.exit_perp_price > 61010.0
    # selling spot -> price pushed BELOW market.
    assert closed.exit_spot_price < 61000.0

    assert provider.spot.calls == 1
    assert provider.perp_calls == 1


# ----------------------------------------------------------------
# close_position - perp leg fails first: nothing touched yet
# ----------------------------------------------------------------


def test_close_position_perp_leg_failure_leaves_position_open_and_untouched():

    provider = FakeDataProvider(perp_fail_on_call=1)
    executor = _executor(provider)

    position = _open_position()

    with pytest.raises(DataProviderError):

        executor.close_position(position, timestamp="t")

    # perp leg is closed FIRST specifically so a failure here never
    # touches the spot leg at all - safe to simply retry.
    assert position.status == "OPEN"
    assert position.exit_time is None
    assert provider.spot.calls == 0


# ----------------------------------------------------------------
# close_position - perp leg closes, spot leg fails: UNBALANCED
# ----------------------------------------------------------------


def test_close_position_spot_leg_failure_marks_unbalanced():

    provider = FakeDataProvider(spot_fail_on_call=1)
    executor = _executor(provider)

    position = _open_position()

    with pytest.raises(UnbalancedPositionError):

        executor.close_position(position, timestamp="t")

    # the perp (short) leg WAS closed - the position is genuinely left
    # naked long on spot, never silently reported as still fully OPEN
    # or fully CLOSED.
    assert position.status == "UNBALANCED"
    assert position.exit_time is None
    assert provider.perp_calls == 1
    assert provider.spot.calls == 1


# ----------------------------------------------------------------
# fee correctness
# ----------------------------------------------------------------


def test_fees_use_the_configured_per_leg_rates():

    provider = FakeDataProvider(spot_price=60000.0, perp_price=60000.0)
    executor = _executor(provider, spot_fee=0.001, futures_fee=0.0005, slippage=0.0)

    spot_fill = executor._fill_spot_leg_buy("BTC/USDT", notional=6000.0)
    perp_fill = executor._fill_perp_leg_open_short("BTC/USDT", spot_fill.quantity)

    assert spot_fill.fee == pytest.approx(spot_fill.price * spot_fill.quantity * 0.001)
    assert perp_fill.fee == pytest.approx(perp_fill.price * perp_fill.quantity * 0.0005)
