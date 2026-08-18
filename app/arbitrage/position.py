from dataclasses import dataclass, field
from typing import Optional

STATUSES = (
    "OPENING",
    "OPEN",
    "UNBALANCED",
    "CLOSING",
    "CLOSED",
)


@dataclass
class ArbitragePosition:
    """
    A delta-neutral funding-arbitrage position: spot long + perpetual
    short on the same symbol/quantity. P&L is meant to come from
    funding_events, not price movement - the two legs are sized to
    cancel each other's price exposure by construction. The one place
    price still matters is the short leg's liquidation risk under
    leverage > 1 - see compute_margin_ratio.

    Two-leg open/close execution (the state machine driving
    OPENING -> OPEN -> CLOSING -> CLOSED, or OPENING/OPEN ->
    UNBALANCED if the legs desync) lives in a later phase - this
    dataclass only carries the field.

    maintenance_margin_rate is captured per-position at open time
    (rather than read from settings at risk-check time) so a later
    change to settings.funding_arb_maintenance_margin_rate never
    silently changes the risk math for an already-open position.
    """

    symbol: str

    leverage: int
    maintenance_margin_rate: float

    entry_time: str

    spot_entry_price: float
    spot_qty: float

    perp_entry_price: float
    perp_qty: float

    margin: float

    status: str = "OPEN"

    cumulative_funding: float = 0.0
    funding_events: list = field(default_factory=list)

    exit_time: Optional[str] = None
    exit_spot_price: Optional[float] = None
    exit_perp_price: Optional[float] = None

    def __post_init__(self):

        if self.status not in STATUSES:

            raise ValueError(
                f"Unknown ArbitragePosition status: {self.status!r} "
                f"(expected one of {STATUSES})"
            )


def compute_liquidation_price(
    entry_price: float,
    leverage: int,
    maintenance_margin_rate: float,
) -> float:
    """
    The perpetual mark price at which the short leg's isolated margin
    ratio (see compute_margin_ratio) reaches 1.0 - derived by solving
    that exact formula for current_price, rather than using the
    simplified public "entry * (1 + 1/leverage - maintenance_margin_rate)"
    approximation Binance documents. The two agree to within ~0.1
    percentage point at maintenance_margin_rate=0.004 (the funding-
    arbitrage measurement used the simplified form); this exact form
    is used here so it stays consistent with compute_margin_ratio by
    construction - see
    test_margin_ratio_at_computed_liquidation_price_is_exactly_one.
    """

    return (
        entry_price
        * (1 + leverage)
        / (leverage * (1 + maintenance_margin_rate))
    )


def compute_margin_ratio(
    position: ArbitragePosition,
    current_price: float,
) -> float:
    """
    Binance-style isolated margin ratio for the short leg:
    maintenance_margin / margin_balance. 0 means no risk, 1.0 means
    liquidation. Only the perp leg's price exposure matters - the
    spot leg is unlevered and carries no liquidation risk.

    Returns float("inf") if margin_balance has already been wiped out
    (<=0) rather than raising or dividing by a non-positive number.
    """

    unrealized_pnl = (
        (position.perp_entry_price - current_price)
        * position.perp_qty
    )

    margin_balance = position.margin + unrealized_pnl

    if margin_balance <= 0:
        return float("inf")

    maintenance_margin = (
        current_price
        * position.perp_qty
        * position.maintenance_margin_rate
    )

    return maintenance_margin / margin_balance


def is_liquidation_warning(
    position: ArbitragePosition,
    current_price: float,
    warning_pct: float,
) -> bool:
    """
    True once the margin ratio has closed to `warning_pct` of the way
    to liquidation (warning_pct=1.0 IS liquidation itself) - the
    trigger a later phase's poller uses for an automatic close,
    independent of funding sign. See
    settings.funding_arb_liquidation_warning_pct.
    """

    return compute_margin_ratio(position, current_price) >= warning_pct


def compute_funding_payment(
    perp_qty: float,
    funding_rate: float,
    mark_price: float,
) -> float:
    """
    Payment received (positive) or paid (negative) by the SHORT leg
    for one funding period. Binance convention: funding_rate > 0
    means longs pay shorts - this strategy's perp leg is short, so a
    positive rate is income here.
    """

    return perp_qty * mark_price * funding_rate


def apply_funding_payment(
    position: ArbitragePosition,
    funding_rate: float,
    mark_price: float,
    timestamp: str,
) -> float:
    """
    Records one funding settlement against `position` in place
    (cumulative_funding + funding_events) and returns the payment
    amount. Pure with respect to everything except the position
    object it mutates - no I/O, no global state.
    """

    payment = compute_funding_payment(
        position.perp_qty,
        funding_rate,
        mark_price,
    )

    position.cumulative_funding += payment

    position.funding_events.append(
        {
            "timestamp": timestamp,
            "funding_rate": funding_rate,
            "mark_price": mark_price,
            "payment": payment,
        }
    )

    return payment
