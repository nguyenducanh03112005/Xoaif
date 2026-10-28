import pandas as pd

from scripts.build_combo_recommendation_f3 import recommendation_screen


def test_screen_requires_all_preregistered_indicators_and_keeps_ranks():
    frame = pd.DataFrame({
        "bundle_discussion_rank": [1, 2, 3],
        "dev_lift": [0.98, 1.2, 1.4],
        "dev_kulczynski": [0.8, 0.6, 0.49],
        "dev_imbalance_ratio": [0.2, 0.4, 0.3],
    })
    result = recommendation_screen(frame)
    assert result.bundle_discussion_rank.tolist() == [1, 2, 3]
    assert result.passes_recommendation_screen.tolist() == [False, True, False]
