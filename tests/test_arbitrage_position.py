import pytest

from app.arbitrage.position import (
    STATUSES,
    ArbitragePosition,
    apply_funding_payment,
    compute_deployable_notional,
    compute_funding_payment,
    compute_liquidation_price,
    compute_margin_ratio,
    consecutive_negative_funding_streak,
    is_liquidation_warning,
)


def _position(
    leverage=5,
    maintenance_margin_rate=0.004,
    entry_price=60000.0,
    perp_qty=1.0,
):

    return ArbitragePosition(
        symbol="BTC/USDT",
        leverage=leverage,
        maintenance_margin_rate=maintenance_margin_rate,
        entry_time="2026-01-01T00:00:00",
        spot_entry_price=entry_price,
        spot_qty=perp_qty,
        perp_entry_price=entry_price,
        perp_qty=perp_qty,
        margin=entry_price * perp_qty / leverage,
    )


# ----------------------------------------------------------------
# ArbitragePosition
# ----------------------------------------------------------------


def test_valid_status_is_accepted():

    position = _position()

    assert position.status == "OPEN"


@pytest.mark.parametrize("status", STATUSES)
def test_every_documented_status_is_accepted(status):

    position = ArbitragePosition(
        symbol="BTC/USDT",
        leverage=1,
        maintenance_margin_rate=0.004,
        entry_time="2026-01-01T00:00:00",
        spot_entry_price=100.0,
        spot_qty=1.0,
        perp_entry_price=100.0,
        perp_qty=1.0,
        margin=100.0,
        status=status,
    )

    assert position.status == status


def test_unknown_status_raises():

    with pytest.raises(ValueError):

        ArbitragePosition(
            symbol="BTC/USDT",
            leverage=1,
            maintenance_margin_rate=0.004,
            entry_time="2026-01-01T00:00:00",
            spot_entry_price=100.0,
            spot_qty=1.0,
            perp_entry_price=100.0,
            perp_qty=1.0,
            margin=100.0,
            status="OPENED",
        )


# ----------------------------------------------------------------
# compute_liquidation_price
# ----------------------------------------------------------------


@pytest.mark.parametrize(
    "leverage, approx_buffer_pct",
    [
        (1, 99.6),
        (3, 32.93),
        (5, 19.6),
        (10, 9.6),
        (20, 4.6),
    ],
)
def test_liquidation_buffer_matches_measurement_within_tolerance(
    leverage, approx_buffer_pct,
):
    """
    Cross-checks the exact margin-ratio-derived formula used here
    against the simplified public approximation the funding-arbitrage
    measurement reported (entry * (1 + 1/leverage - mmr)) - they
    should agree to within a fraction of a percentage point at
    maintenance_margin_rate=0.004, not be identical.
    """

    entry_price = 60000.0
    mmr = 0.004

    liquidation_price = compute_liquidation_price(entry_price, leverage, mmr)

    exact_buffer_pct = (liquidation_price - entry_price) / entry_price * 100

    assert exact_buffer_pct == pytest.approx(approx_buffer_pct, abs=0.5)


def test_liquidation_price_rises_with_lower_leverage():

    entry_price = 60000.0
    mmr = 0.004

    prices = [
        compute_liquidation_price(entry_price, leverage, mmr)
        for leverage in [20, 10, 5, 3, 1]
    ]

    assert prices == sorted(prices)


# ----------------------------------------------------------------
# compute_margin_ratio - the key consistency invariant
# ----------------------------------------------------------------


@pytest.mark.parametrize("leverage", [1, 2, 3, 5, 10, 20])
def test_margin_ratio_at_computed_liquidation_price_is_exactly_one(leverage):

    entry_price = 60000.0
    mmr = 0.004

    position = _position(leverage=leverage, maintenance_margin_rate=mmr, entry_price=entry_price)

    liquidation_price = compute_liquidation_price(entry_price, leverage, mmr)

    ratio = compute_margin_ratio(position, liquidation_price)

    assert ratio == pytest.approx(1.0)


def test_margin_ratio_at_entry_price_equals_leverage_times_mmr():
    """
    At current_price == entry_price, unrealized_pnl is 0, so
    margin_ratio collapses to maintenance_margin / margin =
    (entry*qty*mmr) / (entry*qty/leverage) = mmr * leverage - small
    but not zero, since even a fresh position already carries some
    maintenance margin requirement relative to its margin.
    """

    leverage = 5
    mmr = 0.004

    position = _position(leverage=leverage, maintenance_margin_rate=mmr, entry_price=60000.0)

    ratio = compute_margin_ratio(position, 60000.0)

    assert ratio == pytest.approx(mmr * leverage)


def test_margin_ratio_increases_as_price_rises_against_a_short():

    position = _position(leverage=5, entry_price=60000.0)

    ratios = [
        compute_margin_ratio(position, price)
        for price in [60000, 62000, 64000, 66000, 68000]
    ]

    assert ratios == sorted(ratios)


def test_margin_ratio_decreases_as_price_falls_in_favor_of_a_short():

    position = _position(leverage=5, entry_price=60000.0)

    ratio_at_entry = compute_margin_ratio(position, 60000.0)
    ratio_after_drop = compute_margin_ratio(position, 55000.0)

    assert ratio_after_drop < ratio_at_entry


def test_margin_ratio_is_infinite_once_margin_balance_is_wiped_out():

    position = _position(leverage=5, entry_price=60000.0)

    # margin = 60000*1/5 = 12000; unrealized_pnl <= -12000 once price
    # has risen 12000 above entry (72000+) - margin_balance <= 0.
    ratio = compute_margin_ratio(position, 100000.0)

    assert ratio == float("inf")


# ----------------------------------------------------------------
# is_liquidation_warning
# ----------------------------------------------------------------


def test_is_liquidation_warning_false_near_entry():

    position = _position(leverage=5, entry_price=60000.0)

    assert is_liquidation_warning(position, 60000.0, warning_pct=0.5) is False


def test_is_liquidation_warning_true_at_liquidation_price():

    leverage = 5
    mmr = 0.004
    entry_price = 60000.0

    position = _position(leverage=leverage, maintenance_margin_rate=mmr, entry_price=entry_price)

    liquidation_price = compute_liquidation_price(entry_price, leverage, mmr)

    assert is_liquidation_warning(position, liquidation_price, warning_pct=0.5) is True


def test_is_liquidation_warning_crosses_threshold_partway_to_liquidation():
    """
    margin_ratio is convex in price (it stays small for most of the
    range between entry and liquidation, then rises sharply near the
    end - measured directly: at leverage=5/mmr=0.004, the price
    halfway between entry and liquidation only reaches ratio~0.043,
    not 0.5). So this asserts the crossing at a threshold measured
    from the actual midpoint ratio, rather than assuming linearity.
    """

    leverage = 5
    mmr = 0.004
    entry_price = 60000.0

    position = _position(leverage=leverage, maintenance_margin_rate=mmr, entry_price=entry_price)

    liquidation_price = compute_liquidation_price(entry_price, leverage, mmr)

    midpoint = (entry_price + liquidation_price) / 2
    midpoint_ratio = compute_margin_ratio(position, midpoint)

    assert is_liquidation_warning(position, midpoint, warning_pct=midpoint_ratio - 0.001) is True
    assert is_liquidation_warning(position, midpoint, warning_pct=midpoint_ratio + 0.001) is False
    assert is_liquidation_warning(position, entry_price, warning_pct=midpoint_ratio) is False


# ----------------------------------------------------------------
# funding payments
# ----------------------------------------------------------------


def test_compute_funding_payment_is_qty_times_price_times_rate():

    payment = compute_funding_payment(perp_qty=2.0, funding_rate=0.0001, mark_price=60000.0)

    assert payment == pytest.approx(2.0 * 60000.0 * 0.0001)


def test_positive_funding_rate_is_income_for_the_short():

    payment = compute_funding_payment(perp_qty=1.0, funding_rate=0.0001, mark_price=60000.0)

    assert payment > 0


def test_negative_funding_rate_is_a_cost_for_the_short():

    payment = compute_funding_payment(perp_qty=1.0, funding_rate=-0.0001, mark_price=60000.0)

    assert payment < 0


def test_apply_funding_payment_updates_cumulative_and_history():

    position = _position(entry_price=60000.0, perp_qty=1.0)

    payment = apply_funding_payment(
        position,
        funding_rate=0.0001,
        mark_price=60000.0,
        timestamp="2026-01-01T08:00:00",
    )

    assert payment == pytest.approx(6.0)
    assert position.cumulative_funding == pytest.approx(6.0)
    assert len(position.funding_events) == 1
    assert position.funding_events[0] == {
        "timestamp": "2026-01-01T08:00:00",
        "funding_rate": 0.0001,
        "mark_price": 60000.0,
        "payment": pytest.approx(6.0),
    }


def test_apply_funding_payment_accumulates_across_multiple_periods():

    position = _position(entry_price=60000.0, perp_qty=1.0)

    apply_funding_payment(position, 0.0001, 60000.0, "t1")
    apply_funding_payment(position, -0.00005, 61000.0, "t2")
    apply_funding_payment(position, 0.0002, 59000.0, "t3")

    expected = (
        1.0 * 60000.0 * 0.0001
        + 1.0 * 61000.0 * -0.00005
        + 1.0 * 59000.0 * 0.0002
    )

    assert position.cumulative_funding == pytest.approx(expected)
    assert len(position.funding_events) == 3
    assert [e["timestamp"] for e in position.funding_events] == ["t1", "t2", "t3"]


# ----------------------------------------------------------------
# compute_deployable_notional
# ----------------------------------------------------------------


def test_deployable_notional_at_leverage_one_is_half_capital():

    assert compute_deployable_notional(10000.0, 1) == pytest.approx(5000.0)


@pytest.mark.parametrize(
    "leverage, expected",
    [
        (1, 5000.0),
        (3, 7500.0),
        (5, 8333.333333),
        (10, 9090.909091),
    ],
)
def test_deployable_notional_matches_measured_capital_efficiency_table(
    leverage, expected,
):

    assert compute_deployable_notional(10000.0, leverage) == pytest.approx(
        expected, abs=0.01,
    )


def test_deployable_notional_increases_with_leverage():

    values = [
        compute_deployable_notional(10000.0, leverage)
        for leverage in [1, 2, 3, 5, 10, 20]
    ]

    assert values == sorted(values)
    assert values[-1] < 10000.0


# ----------------------------------------------------------------
# consecutive_negative_funding_streak
# ----------------------------------------------------------------


def test_streak_is_zero_for_empty_history():

    assert consecutive_negative_funding_streak([]) == 0


def test_streak_is_zero_when_most_recent_is_positive():

    events = [
        {"funding_rate": -0.0001},
        {"funding_rate": -0.0001},
        {"funding_rate": 0.0001},
    ]

    assert consecutive_negative_funding_streak(events) == 0


def test_streak_counts_only_the_trailing_negative_run():

    events = [
        {"funding_rate": 0.0001},
        {"funding_rate": -0.0001},
        {"funding_rate": -0.0001},
        {"funding_rate": -0.0001},
    ]

    assert consecutive_negative_funding_streak(events) == 3


def test_streak_resets_after_a_positive_settlement_in_the_middle():

    events = [
        {"funding_rate": -0.0001},
        {"funding_rate": -0.0001},
        {"funding_rate": 0.0001},
        {"funding_rate": -0.0001},
    ]

    assert consecutive_negative_funding_streak(events) == 1


def test_zero_funding_rate_does_not_count_as_negative():

    events = [
        {"funding_rate": -0.0001},
        {"funding_rate": 0.0},
    ]

    assert consecutive_negative_funding_streak(events) == 0
