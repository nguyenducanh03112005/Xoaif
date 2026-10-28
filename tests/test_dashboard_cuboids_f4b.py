import pandas as pd
import pytest

from scripts.build_dashboard_cuboids_f4b import suppress_2d


def test_primary_and_complementary_suppression_in_two_child_quarter():
    cube = pd.DataFrame({
        "quarter": ["q1", "q1", "q2", "q2"],
        "segment": ["a", "b", "a", "b"],
        "orders": [10, 100, 100, 100],
        "customers": [10, 50, 50, 50],
        "recognized_revenue_vnd": [1000, 10000, 20000, 30000],
    })
    result, meta = suppress_2d(cube, dimension="segment")
    assert result[result.quarter == "q1"].suppressed.all()
    assert result.loc[result.quarter == "q1", "recognized_revenue_vnd"].isna().all()
    assert meta["primary"] == 1
    assert meta["complementary"] == 1


def test_threshold_is_locked_at_30():
    with pytest.raises(ValueError):
        suppress_2d(pd.DataFrame(), dimension="segment", min_n=29)
