from pathlib import Path


def test_arbitrage_modules_never_reference_real_order_placement():
    """
    Parallel equivalent of tests/test_live_trader.py's
    test_live_execution_modules_never_reference_real_order_placement,
    scoped to app/arbitrage/ instead of app/execution/live_*.py -
    that test's glob only covers app/execution/, so it does not (and
    structurally cannot) protect this separate module. See the
    funding-arbitrage plan's Faz 4/güvenlik section.

    Unlike the app/execution/ equivalent, there is no "live_*" naming
    convention in app/arbitrage/, so this globs EVERY .py file in the
    directory (not a name pattern) - a future file added here without
    a special name is still automatically covered.

    Neither FundingDataProvider (the only module that constructs a
    ccxt exchange instance) nor any other file in this package may
    reference a real order-placement ccxt call or API credentials -
    this whole module must remain structurally incapable of sending a
    real order, exactly like the live-trading path.
    """

    forbidden = (
        "create_order",
        "create_market_order",
        "create_limit_order",
        "apiKey",
        "secret",
    )

    arbitrage_dir = Path(__file__).resolve().parent.parent / "app" / "arbitrage"

    scanned_files = list(arbitrage_dir.glob("*.py"))

    # Guards against the glob silently matching nothing (e.g. a
    # typo'd pattern, or the directory being renamed/moved) and this
    # test passing vacuously. There are 7 files in app/arbitrage/ as
    # of this writing; 5 leaves headroom for future additions without
    # needing to bump this floor every time.
    assert len(scanned_files) >= 5

    for path in scanned_files:

        source = path.read_text(encoding="utf-8")

        for keyword in forbidden:
            assert keyword not in source, f"{keyword!r} found in {path.name}"
