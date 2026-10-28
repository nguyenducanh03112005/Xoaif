# Pancake POS API notes

Last reviewed: 2026-10-28. Sources below are Pancake documentation. A local configuration was found and read-only API calls succeeded. Raw orders are stored only in the ignored local data folder.

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
- Ordering guarantees and total-count semantics beyond the observed snapshot.
- Date filters and whether updated_at is reliable for incremental sync.
- Whether the one-page order behavior and pagination totals remain stable over time; the current documentation now describes pagination, but the live verification was limited to the locked snapshot.
- Inventory, order-detail, conversation, and message endpoint schemas and shop-specific availability. No conversation/message endpoint was identified in the current POS Open API catalog.
- Whether status history is complete and retained for all historical orders; what `status_history.updated_at` means; and whether actual collection/refund event timestamps are available.
- Rate limits, retry guidance, deletion behavior, and timezone semantics.

Do not implement incremental extraction, point-in-time labels, or revenue mappings until their behavior is checked against the reference documentation and an authorized live request.

## Official sources

- [Open API overview](https://pos.pancake.vn/developers/api/en)
- [Open API endpoint index](https://pos.pancake.vn/developers/api/llms.txt)
- [Customer endpoint reference](https://pos.pancake.vn/developers/api/customer.md)
- [Product endpoint reference](https://pos.pancake.vn/developers/api/product.md)
- [eCommerce evaluation reference](https://pos.pancake.vn/developers/api/ecommerce.md)
- [Ads Manager endpoint reference](https://pos.pancake.vn/developers/api/ads-manager.md)

## Metadata-only probe — 2026-10-28

The owner approved a GET-only metadata probe. `scripts/probe_endpoints.py` called only the five explicitly allowlisted endpoints; it kept a spread-page sample of at most 500 records in RAM, emitted only aggregate JSON, and did not retain or log API response values. The HMAC comparison used the locked DEV warehouse keys in the project namespaces; match rates below are for sampled records, not full endpoint coverage.

| Endpoint | HTTP / total entries | Sample and DEV match | PII / order join / response label | Decision before ingestion |
|---|---:|---|---|---|
| `GET /shops/{SHOP_ID}/products/variations` | 200 / 832 | 482 sampled; 394 matched DEV product keys (81,74%) | No direct customer PII observed in sampled field names; joins to product dimension by `product_id`, not directly to an order; no response label | Present and linkable on sample, but current catalog is not verified as point-in-time product history. Requires Claude review and a field allowlist. |
| `GET /shops/{SHOP_ID}/customers` | 200 / 13.232 | 482 sampled; 194 matched DEV customer keys on `customer_id` (40,25%); top-level `id` had no matches | Direct identifiers/free-text fields present; sampled `customer_id` can be HMAC-joined to the DEV customer key, not directly to an order; no response label | Present and partially linkable on sample. Do not ingest pending review and explicit field/HMAC rules. |
| `GET /shops/{SHOP_ID}/shopee/evaluate` | 200 / 0 | No sample; rating distribution not available | PII, join key, and label availability cannot be assessed from an empty response | Skipped. No evaluation records available in this probe. |
| `GET /shops/{SHOP_ID}/ads_manager/ad_accounts` | 200 / 0 | No sample; no order join key confirmed | PII and label availability cannot be assessed from an empty response; no order join observed | Skipped. |
| `GET /shops/{SHOP_ID}/ads_manager/campaigns_v2` | 200 / 0 | No sample; no order join key confirmed | PII and label availability cannot be assessed from an empty response; no order join observed | Skipped. |

For products and customers, the reported date range and field-level non-null rates describe only the spread-page sample. Zero matches for Shopee evaluations or ads endpoints is not evidence that these data types never existed historically. Customer/profile and product catalog snapshots may have changed since orders were created. No endpoint data has been ingested; `config/field_allowlist.yaml` remains unchanged. The sanitized aggregate is in [pancake_endpoint_probe_20261028.json](pancake_endpoint_probe_20261028.json). Product/customer sampled matches are not proof that all records join, nor are they order-level joins.

The allowlist intentionally excludes customer detail, point logs, and customer notes endpoints. The client continues to reject all non-GET methods and any path outside the exact approved endpoint list.
