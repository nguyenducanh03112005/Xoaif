"""Check the offline dashboard's read-only aggregate data contract without AppTest."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app" / "streamlit_app.py"
TABLES = ROOT / "outputs" / "tables"
METRICS = ROOT / "outputs" / "metrics"
FORBIDDEN_KEYS = {
    "customer_key", "customer_id", "order_key", "order_id", "phone", "phone_number",
    "email", "address", "shipping_address", "api_key", "access_token",
}


def _literal_reader_calls(tree: ast.AST, name: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                found.add(node.args[0].value)
    return found


def _reject_sensitive_keys(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold()
            if normalized in FORBIDDEN_KEYS:
                raise ValueError(f"Sensitive field present in aggregate JSON schema: {path}.{key}")
            _reject_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, f"{path}[{index}]")


def _check_small_count_suppression(name: str, frame: pd.DataFrame) -> None:
    count_columns = {
        "dashboard_product_orders.csv": ("order_count",),
        "dashboard_status_counts.csv": ("order_count",),
        "gift_line_audit.csv": ("line_count", "distinct_order_count", "gift_line_count"),
    }.get(name, ())
    for column in count_columns:
        counts = pd.to_numeric(frame[column], errors="coerce").dropna()
        if (counts < 10).any():
            raise ValueError(f"Unsuppressed count below 10 in dashboard aggregate {name}")

    if name == "dashboard_product_orders.csv":
        other = frame.loc[frame["product_name"] == "Khác — từng sản phẩm dưới 10 lượt đơn"]
        if len(other) > 1 or (
            not other.empty and pd.notna(other.iloc[0]["order_count"])
            and other.iloc[0]["order_count"] != ""
        ):
            raise ValueError("Low-volume product aggregation is not in the expected shape")


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(APP))
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if imports.intersection({"requests", "httpx", "urllib", "socket", "pancake"}):
        raise ValueError("Dashboard imports a network client; expected local outputs only")
    if "data/raw" in source.replace("\\", "/") or "data/restricted" in source.replace("\\", "/"):
        raise ValueError("Dashboard source references raw or restricted data")

    tabs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "st"
        and node.func.attr == "tabs" and node.args
    ]
    if len(tabs) != 1:
        raise ValueError("Expected one explicit dashboard tab declaration")
    tab_names = ast.literal_eval(tabs[0].args[0])
    if len(tab_names) != 5:
        raise ValueError(f"Expected five dashboard tabs, found {len(tab_names)}")

    csv_names = _literal_reader_calls(tree, "read_csv")
    json_names = _literal_reader_calls(tree, "read_json")
    if len(csv_names) != 10 or len(json_names) != 6:
        raise ValueError(f"Unexpected dashboard inputs: {len(csv_names)} CSV and {len(json_names)} JSON")

    rows_checked = 0
    for name in sorted(csv_names):
        path = TABLES / name
        if not path.is_file():
            raise FileNotFoundError(f"Dashboard aggregate is missing: {name}")
        frame = pd.read_csv(path)
        if frame.empty:
            raise ValueError(f"Dashboard aggregate is empty: {name}")
        bad = FORBIDDEN_KEYS.intersection(str(column).casefold() for column in frame.columns)
        if bad:
            raise ValueError(f"Sensitive identifier field in dashboard table {name}")
        _check_small_count_suppression(name, frame)
        rows_checked += len(frame)

    for name in sorted(json_names):
        path = METRICS / name
        if not path.is_file():
            raise FileNotFoundError(f"Dashboard metric is missing: {name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Dashboard metric must be an aggregate object: {name}")
        _reject_sensitive_keys(payload, name)

    print(
        f"Dashboard smoke passed: {len(tab_names)} tabs, {len(csv_names)} aggregate CSVs, "
        f"{len(json_names)} aggregate JSONs, {rows_checked} aggregate rows checked; no AppTest or API call."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
