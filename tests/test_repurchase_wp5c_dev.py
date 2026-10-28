import pandas as pd

from scripts.evaluate_repurchase_wp5c_dev import _train_mapping, _score_validation, _bins


def _frame(counts):
    rows = []
    for frequency, recency, n, positives in counts:
        rows += [{"frequency": frequency, "recency_days": recency, "label_returned": int(i < positives)}
                 for i in range(n)]
    return pd.DataFrame(rows)


def test_sparse_recency_bands_merge_in_train_only_until_minimum():
    train = _frame([
        (1, 10, 120, 12), (1, 60, 20, 2), (1, 120, 25, 2), (1, 240, 30, 3),
        (2, 10, 120, 20), (2, 60, 120, 18), (2, 120, 120, 15), (2, 240, 120, 12),
        (3, 10, 120, 30), (3, 60, 120, 25), (3, 120, 120, 20), (3, 240, 120, 15),
    ])
    _, audit = _train_mapping(train)
    row1 = [row for row in audit if row["frequency_bin"] == "1"]
    assert sum(row["n"] for row in row1) == 195
    assert all(row["n"] >= 100 for row in row1[:-1]) or len(row1) == 1
    assert all("rate" in row for row in audit)


def test_validation_scores_use_rates_learned_from_train_cells():
    train = _frame([(1, 10, 120, 12), (2, 10, 120, 24), (3, 10, 120, 36)])
    mapping, audit = _train_mapping(train)
    valid = _bins(pd.DataFrame({"frequency": [1, 2, 3], "recency_days": [10, 10, 10]}))
    scores = _score_validation(valid, mapping, audit, train.label_returned.mean())
    assert scores.tolist() == [0.1, 0.2, 0.3]
