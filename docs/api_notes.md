# Pancake POS API notes

Last reviewed: 2026-10-24. Sources below are Pancake documentation. A local configuration was found and read-only API calls succeeded. Raw orders are stored only in the ignored local data folder.

## Verified from official documentation

- Base URL is https://pos.pages.fm/api/v1.
- Authentication for the POS Open API uses the api_key query parameter.
- GET /shops is the documented connection check.
- GET /shops/{SHOP_ID}/orders is the documented orders endpoint.
- filter_status[] is documented for filtering orders by status.
- Status meanings include 3 = received/delivered, 16 = collected money, 5 = returned, 6 = canceled, and 7 = recently deleted. The documentation warns that shops may skip stages and that returned orders have a separate status enum.
- Pancake documentation warns that the shop API key has full read/write administrative access and cannot be limited. Treat it as a high-impact secret. The project code exposes GET only.

## Verified by local read-only calls

- A live GET /shops request succeeded with the local configuration; only the number of visible shops and whether the configured shop ID was present were printed.
- One GET /shops/{SHOP_ID}/orders filtered to documented status 0 was inspected in memory. The response exposed `data`, `success`, `page_number`, `page_size`, `total_pages`, and `total_entries`; the order object exposed `status_history` and `histories`. Only field names and JSON types were printed; the response was not saved and values were not printed.
- In the inspected order shape, `status_history` contained `status`, `old_status`, and `updated_at`, plus editor-related fields. This establishes only that a history-shaped field was returned for one order; it does not establish completeness or timestamp semantics. See docs/point_in_time.md.
- Live probe sent `page_number` and `page_size` for the first two unfiltered pages; both were echoed and `page_size=20` was respected. The two pages had different order IDs. No order values were printed by the probe.
- The initial 12,009-order snapshot was later found to have a page checksum mismatch; all of its counts are obsolete and must not be used. The replacement snapshot `20261024T052943Z` contains 12,011 orders across 601 pages and is the current locked source; see `docs/PROGRESS.md` for its verification results.

## Not yet verified

- Whether an account-level, read-only API key is accepted by the POS Open API. Do not assume the account key described for other Pancake integrations works here.
- Ordering guarantees and total-count semantics beyond the observed snapshot. Live probing confirmed `page_number` and `page_size` for the first two pages.
- Date filters and whether updated_at is reliable for incremental sync.
- Order detail, product, customer, inventory, review, and conversation endpoint schemas.
- Whether status history is complete and retained for all historical orders; what `status_history.updated_at` means; and whether actual collection/refund event timestamps are available.
- Rate limits, retry guidance, deletion behavior, and timezone semantics.
- The parsed official reference does not expose order pagination request parameters. Their behavior is supported by the limited live probe and snapshot integrity checks, not by a published official parameter specification.

Do not implement incremental extraction, point-in-time labels, or revenue mappings until their behavior is checked against the reference documentation and an authorized live request.

## Official sources

- [Open API overview](https://docs.pancake.biz/pos/st-f13/st-p1?lang=en)
- [Get an API key and authenticate](https://docs.pancake.biz/pos/st-f13/st-p2?lang=en)
- [Order status and processing flow](https://docs.pancake.biz/pos/st-f13/st-p3?lang=en)
