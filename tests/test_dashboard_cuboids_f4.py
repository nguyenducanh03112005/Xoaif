import pandas as pd

from scripts.build_dashboard_cuboids_f4 import apply_suppression


def test_primary_suppression_hides_all_measures_below_30():
    cube = pd.DataFrame({
        "quarter": ["q1", "q1", "q1", "q1"],
        "channel": ["a", "a", "b", "b"],
        "rfm": ["x", "y", "x", "y"],
        "orders": [10, 100, 100, 100],
        "customers": [10, 40, 40, 40],
        "recognized_revenue_vnd": [1000, 10_000, 20_000, 30_000],
    })
    safe, metrics = apply_suppression(cube, dimensions=["quarter", "channel", "rfm"])
    assert safe.loc[0, "suppressed_primary"]
    assert safe.loc[0, ["orders", "customers", "recognized_revenue_vnd"]].isna().all()
    assert metrics["suppression_rate"] >= .5


def test_complementary_suppression_prevents_single_hidden_child_residual():
    cube = pd.DataFrame({
        "quarter": ["q1"] * 6,
        "channel": ["a", "a", "a", "b", "b", "b"],
        "rfm": ["x", "y", "z"] * 2,
        "orders": [10, 100, 100, 100, 100, 100],
        "customers": [10, 40, 40, 40, 40, 40],
        "recognized_revenue_vnd": [1000, 10_000, 20_000, 30_000, 40_000, 50_000],
    })
    safe, metrics = apply_suppression(cube, dimensions=["quarter", "channel", "rfm"])
    assert metrics["suppressed_complementary"] >= 1
    for _, group in safe.groupby(["quarter", "channel"]):
        hidden = int(group.suppressed.sum())
        assert hidden == 0 or hidden >= 2
    for _, group in safe.groupby(["quarter", "rfm"]):
        hidden = int(group.suppressed.sum())
        assert hidden == 0 or hidden >= 2
