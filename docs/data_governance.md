# Data governance

## Data classes and storage

- Raw API responses may contain direct identifiers and are restricted to local data/raw/. Never commit or share them.
- Pseudonymous customer IDs, order-level records, labels, model scores, and cleaned text remain in data/restricted/; HMAC identifiers are sensitive because they link a customer's history.
- Only reviewed aggregates belong in data/shared/ or deliverables. Exclude customer/order IDs, record-level text, and combinations that could reveal small groups.
- `config/field_allowlist.yaml` permits only the Day 1 fields reviewed against the order schema: order ID, `inserted_at`, current status, customer ID, and item `product_id`. The three identifiers are HMACed before warehouse storage. Money, free text, contact data, current customer rollups, and status history remain excluded.

## Secrets

Store credentials in local xoaif.env, excluded from git. Never print or log secrets, raw request URLs, API response bodies, or exception text from HTTP libraries. Rotate a key if exposure is suspected.

Pancake's POS Open API documentation says its shop API key has full read/write administrative access. The project client therefore implements GET requests only. Do not use that key for any unrelated operation.

## Access, retention, deletion

At project start, record who can access raw/restricted data and the approved retention period. **Owner decision (2026-10-24):** retain raw through the defense, then delete raw and keep only an anonymized processed copy. Do not delete raw before the defense. Record deletion date, scope, and any reason for retention.

## Text and external services

Free text is sensitive even after obvious names/phones are removed. Keep it in restricted storage. Do not send text to external LLM providers until the provider, data fields, retention/training terms, and processing location have been reviewed and the user has approved.

## Shared outputs

Define a minimum group size and complementary suppression policy before publishing. Dashboard filters must not allow a user to infer a hidden cell by comparing nearby queries.
