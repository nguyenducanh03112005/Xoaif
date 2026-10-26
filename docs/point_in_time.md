# Point-in-time data feasibility

## Current decision

The locked analysis source is snapshot `20261024T052943Z`. The earlier
12,009-order snapshot `20261023T174441Z` had a page checksum mismatch; every
metric and profile derived from it is obsolete. Do not use those figures as
current evidence.

The project owner decided that source timestamps are UTC and should be
converted to `Asia/Ho_Chi_Minh` for local-date analysis. This decision is based
on a dashboard comparison described by the owner; the comparison artifact is
not stored in the repository.

The owner also decided that only current status `3` is a valid purchase and
that `status_history` must not be used as a feature or label. Therefore this
project has not reconstructed historical status at a customer observation
time. The Day 1 warehouse uses only the current status for descriptive counts.

## Remaining limitations

- The API snapshot has no transaction token; changes during extraction cannot be
  ruled out solely from the local page checksums.
- Status-history event-time meaning, completeness, ordering, and tied timestamp
  behavior have not been independently resolved. No history field is included
  in the Day 1 allowlist.
- The parsed official reference does not publish the observed pagination
  request parameters. `page_number` and `page_size` were confirmed by a limited
  live probe and snapshot checks, not by a published parameter specification.
- Money, refund, return, and settlement semantics are not approved, so no
  historical revenue or monetary customer feature is calculated.

Direct identifiers, contact details, free text, payment/tracking links, and
editor identity remain excluded. The Day 1 allowlist is in
`config/field_allowlist.yaml`; IDs are HMACed before entering restricted DuckDB.

For any later historical feature, record whether the source provides an event
timestamp, an observation timestamp, a history of prior values, and whether the
value can be reconstructed at T. If no usable history exists, exclude that
feature. Do not load test labels before the final evaluation.
