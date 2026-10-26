# Data protocol: single source of truth

Status: locked for snapshot `20261024T052943Z`; exact configuration digest is in `config/split.lock.json`.

## Time and snapshot

- Convert timestamps to Asia/Ho_Chi_Minh for date-based analysis while retaining raw UTC values when supplied.
- DATA_CUTOFF is the exclusive start of the day after the last complete local date in a frozen snapshot. Store the extraction timestamp separately.
- Calendar intervals are half-open [start, end). W is always a duration in calendar days.
- A new extraction is a new run. Do not silently move a locked cutoff or reuse a test window after test labels have been loaded.

## Owner amendment: business opening date

- On 2026-10-25 the owner confirmed that Xoaif Garden began operating on
  2024-04-01 (Asia/Ho_Chi_Minh local date).
- Orders before `analysis_start=2024-04-01` are retained unchanged in raw and
  excluded from all behavioral, RFM, label, basket, and recorded-sales analyses.
- This rule is recorded in `config/amendment_01_analysis_start.yaml`; its
  SHA-256 and the active `split.lock.json` SHA-256 are sealed in the amendment
  sidecar. `config/split.yaml` remains unchanged.
- The effective development interval is
  `[2024-04-01, 2025-10-22)`. No labels or test behavior are used. For rows at
  or after `test_start`, the profiling code reads only `inserted_at` to exclude
  the row before accessing any other field.

## Development and test

Before behavior statistics are examined, lock the candidate sets, W, and snapshot identity. The owner-approved primary evaluation is `N=180`, `L=7`, `W=180`, with test T dates in `[2025-10-22, 2026-04-20)`. The primary test eligibility floor is 30 distinct customers.

- The reserved boundary for the largest development sensitivity is `DATA_CUTOFF − (max(W_candidates) + max(N_candidates) + max(L_candidates))`; for this run it is `2024-10-17`. Development labels must also satisfy `T + N + L < test_start` so their outcome window cannot enter the primary test period.
- The locked primary dates are `test_start=2025-10-22` and `test_end_exclusive=2026-04-20`. No alternative N/W window is a test evaluation.
- `N=365`, `W=90`, and `W=365` are development-only sensitivities. Their EDA and any sensitivity calculations may use only development dates strictly before `test_start`; development labels must be fully observed before `test_start`.
- The reserved test region may expose only eligibility counts, never labels or purchase behavior, before final evaluation. Before the lock, eligibility was counted at the candidate starts in `config/split.yaml`; the N=365 count is a feasibility check for the alternative plan only.
- Development EDA stops strictly before `test_start`. Training and validation use forward-in-time folds and purge at least `N+L` days between the last train T and the next validation/test T.
- Lock the split config hash and write access_log entries for eligibility counts and label loads. Only the final evaluation step may load test labels, once.
- Record the exact `config/split.yaml` SHA-256 and lock timestamp in `config/split.lock.json`. Keeping the digest in a sidecar avoids a self-referential hash; changing the YAML after approval invalidates the sidecar and requires a new approval.

## Eligibility and label

customer_eligibility_rule: at least one owner-valid purchase (current status 3), with a non-missing customer ID and local purchase date strictly before T; count distinct HMAC-pseudonymized customers.

The preflight threshold is 30 eligible customers. It is an operational floor to
avoid reporting metrics from a very small cohort; it is not a statistical power
guarantee. The N=180 and N=365 feasibility counts used different candidate
starts, so their counts are not a like-for-like comparison.

Proposed label: a customer has at least one valid repeat order created in (T, T+N], with status assessed at label_asof = T+N+L. Freeze the label there; never revise it using later status.

The owner approved N=180, L=7, status-3-only purchase validity, and the snapshot identity. Status history is excluded from features and labels; its unresolved timestamp semantics remain a limitation. No test labels have been loaded.

Known seasonal limitation: the 180-day repeat-label horizon (`N=180`) can
undercount customers who return mainly for holidays on an approximately annual
cycle. Evaluate `N=365` as a sensitivity using the development set. `W=365` is
also a development-only test-window-length sensitivity; it does not change the
label horizon. Do not open a second test.
