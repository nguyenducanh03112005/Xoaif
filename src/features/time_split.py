"""Date-only, leakage-aware reservation of a temporal test window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import hashlib


@dataclass(frozen=True)
class TestWindow:
    """Half-open test interval containing exactly window_days calendar days."""

    start: date
    end_exclusive: date

    @property
    def days(self) -> int:
        return (self.end_exclusive - self.start).days


@dataclass(frozen=True)
class ReservedSplit:
    """Candidate-safe test reservation for an immutable snapshot."""

    data_cutoff: date
    window_days: int
    n_candidates_days: tuple[int, ...]
    l_candidates_days: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.window_days <= 0:
            raise ValueError("window_days must be positive.")
        if not self.n_candidates_days or not self.l_candidates_days:
            raise ValueError("N and L candidate sets must not be empty.")
        if any(days <= 0 for days in self.n_candidates_days):
            raise ValueError("N candidates must be positive day counts.")
        if any(days < 0 for days in self.l_candidates_days):
            raise ValueError("L candidates cannot be negative.")

    @property
    def dev_cutoff(self) -> date:
        """First date excluded from development and reserved for possible test."""
        reserve_days = (
            self.window_days
            + max(self.n_candidates_days)
            + max(self.l_candidates_days)
        )
        return self.data_cutoff - timedelta(days=reserve_days)

    def test_window(self, n_days: int, l_days: int) -> TestWindow:
        """Return a locked-candidate window and verify it stays in reservation."""
        if n_days not in self.n_candidates_days:
            raise ValueError("N is not in the locked candidate set.")
        if l_days not in self.l_candidates_days:
            raise ValueError("L is not in the locked candidate set.")

        end_exclusive = self.data_cutoff - timedelta(days=n_days + l_days)
        start = end_exclusive - timedelta(days=self.window_days)
        if start < self.dev_cutoff:
            raise ValueError("Candidate test window extends into development.")
        return TestWindow(start=start, end_exclusive=end_exclusive)


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for a configuration or snapshot manifest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_train_gap(
    *,
    max_train_t: date,
    test_start: date,
    n_days: int,
    l_days: int,
) -> None:
    """Ensure the last training label's as-of date does not cross test start."""
    if max_train_t >= test_start:
        raise ValueError("Training T must be earlier than test_start.")
    if (test_start - max_train_t).days < n_days + l_days:
        raise ValueError("Train/test gap must be at least N + L calendar days.")
