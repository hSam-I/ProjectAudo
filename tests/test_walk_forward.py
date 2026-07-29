import pandas as pd

from app.optimization.walk_forward import WalkForwardAnalyzer


def test_walk_forward():

    df = pd.DataFrame({
        "close": range(300)
    })

    analyzer = WalkForwardAnalyzer(
        train_size=100,
        test_size=50,
    )

    windows = analyzer.generate_windows(df)

    assert len(windows) == 4