from datetime import date, timedelta

import pytest

from features.time_split import ReservedSplit, validate_train_gap


def test_candidate_windows_fit_inside_reserved_region() -> None:
    split = ReservedSplit(
        data_cutoff=date(2026, 10, 1),
        window_days=30,
        n_candidates_days=(60, 90),
        l_candidates_days=(14, 30),
    )

    assert split.dev_cutoff == date(2026, 5, 4)
    window = split.test_window(60, 14)
    assert window.days == 30
    assert window.start >= split.dev_cutoff
    assert window.end_exclusive == date(2026, 7, 19)


def test_test_window_uses_half_open_calendar_days() -> None:
    split = ReservedSplit(
        data_cutoff=date(2026, 10, 1),
        window_days=45,
        n_candidates_days=(90,),
        l_candidates_days=(30,),
    )
    window = split.test_window(90, 30)

    assert window.end_exclusive - window.start == timedelta(days=45)


def test_train_gap_rejects_overlap_or_short_gap() -> None:
    with pytest.raises(ValueError, match="at least N \\+ L"):
        validate_train_gap(
            max_train_t=date(2026, 1, 1),
            test_start=date(2026, 4, 1),
            n_days=90,
            l_days=30,
        )


def test_candidates_cannot_be_changed_after_reservation() -> None:
    split = ReservedSplit(
        data_cutoff=date(2026, 10, 1),
        window_days=30,
        n_candidates_days=(60,),
        l_candidates_days=(14,),
    )
    with pytest.raises(ValueError, match="candidate set"):
        split.test_window(90, 14)
