# Shared dashboard release contract

The Streamlit app reads only four fixed CSV names from `data/shared/` and
requires `data/shared/release_manifest.json` with `status: approved`. The
manifest is created only after the CP2 release review; the app never reads
`data/raw`, `data/restricted`, or a caller-supplied path.

Example manifest shape (values are placeholders):

```json
{
  "status": "approved",
  "run_id": "<snapshot-and-code-run-id>",
  "min_group_size": 5,
  "datasets": {
    "sales": {
      "file": "sales_daily.csv",
      "sha256": "<64 lowercase hex characters>",
      "columns": ["period", "order_count", "amount"]
    }
  }
}
```

`segments`, `combos`, and `issues` use the fixed names in
`src/app/dashboard.py`. Each registered file must match its checksum and exact
column list. Columns suggesting direct identifiers, contact details, free
text, links, or editor identity are rejected. Rows with a registered count
below `min_group_size` are hidden in full. The project owner must set the
threshold and review differencing risk before creating an approved manifest.

No release manifest or CSV exists yet. The dashboard therefore shows a clear
empty state instead of synthetic results.
