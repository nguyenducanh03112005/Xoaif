"""Streamlit demo that reads only approved, checksummed shared aggregates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = PROJECT_ROOT / "data" / "shared"
MANIFEST_PATH = SHARED_DIR / "release_manifest.json"

DATASETS = {
    "sales": ("Doanh số", "sales_daily.csv"),
    "segments": ("Phân khúc", "segment_summary.csv"),
    "combos": ("Combo", "association_rules.csv"),
    "issues": ("Vấn đề sản phẩm", "issue_summary.csv"),
}

_FORBIDDEN_COLUMN_PARTS = {
    "id",
    "name",
    "phone",
    "mobile",
    "email",
    "address",
    "full_name",
    "customer_name",
    "free_text",
    "note",
    "comment",
    "message",
    "content",
    "conversation",
    "editor",
    "link",
    "url",
    "raw",
}
_SAFE_LABEL_COLUMNS = {"segment_name", "issue_name", "product_name", "category_name"}


class ReleaseError(ValueError):
    """The shared output release does not meet its safety contract."""


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        raise ReleaseError("No reviewed shared-output release is available.")
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ReleaseError("The shared-output release manifest is invalid.") from None
    if not isinstance(manifest, dict) or manifest.get("status") != "approved":
        raise ReleaseError("The shared-output release has not been approved.")
    min_group_size = manifest.get("min_group_size")
    if isinstance(min_group_size, bool) or not isinstance(min_group_size, int) or min_group_size < 5:
        raise ReleaseError("The release manifest has no valid minimum group size.")
    if not isinstance(manifest.get("datasets"), dict):
        raise ReleaseError("The release manifest has no dataset registry.")
    return manifest


def _safe_columns(columns: list[str]) -> bool:
    for column in columns:
        normalized = re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_")
        if normalized in _SAFE_LABEL_COLUMNS:
            continue
        parts = set(normalized.split("_"))
        if parts & _FORBIDDEN_COLUMN_PARTS or normalized.endswith("_id"):
            return False
    return True


def _load_dataset(manifest: dict[str, Any], dataset_key: str) -> pd.DataFrame:
    _, filename = DATASETS[dataset_key]
    spec = manifest["datasets"].get(dataset_key)
    if not isinstance(spec, dict) or spec.get("file") != filename:
        raise ReleaseError("This dataset is not registered in the approved release.")
    approved_columns = spec.get("columns")
    checksum = spec.get("sha256")
    if (
        not isinstance(approved_columns, list)
        or not all(isinstance(item, str) for item in approved_columns)
        or not _safe_columns(approved_columns)
        or not isinstance(checksum, str)
        or not re.fullmatch(r"[0-9a-f]{64}", checksum)
    ):
        raise ReleaseError("The registered dataset schema or checksum is invalid.")

    path = SHARED_DIR / filename
    try:
        content = path.read_bytes()
    except OSError:
        raise ReleaseError("The registered shared dataset is missing.") from None
    if hashlib.sha256(content).hexdigest() != checksum:
        raise ReleaseError("The shared dataset checksum does not match its manifest.")

    try:
        frame = pd.read_csv(path)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError):
        raise ReleaseError("The shared dataset could not be read as CSV.") from None
    if list(frame.columns) != approved_columns:
        raise ReleaseError("The shared dataset columns differ from the approved schema.")
    if not _safe_columns(list(frame.columns)):
        raise ReleaseError("The shared dataset contains a restricted column name.")

    count_columns = [
        column
        for column in frame.columns
        if column.lower() in {"count", "n", "orders", "customers", "baskets"}
        or column.lower().endswith("_count")
    ]
    if not count_columns:
        raise ReleaseError("The dataset has no group-size column for suppression.")
    hidden = pd.Series(False, index=frame.index)
    for column in count_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or (values < 0).any():
            raise ReleaseError("A group-size column contains invalid counts.")
        hidden |= values < manifest["min_group_size"]
    frame.loc[hidden, :] = pd.NA
    return frame


def main() -> None:
    st.set_page_config(page_title="Xoaif Garden · Phân tích bán hàng", layout="wide")
    st.title("Xoaif Garden · Phân tích bán hàng")
    st.caption("Dashboard chỉ đọc các bảng tổng hợp đã duyệt trong data/shared.")

    try:
        manifest = _load_manifest()
    except ReleaseError as exc:
        st.info(str(exc))
        st.caption("Kết quả sẽ xuất hiện sau khi CP2 duyệt dữ liệu shared.")
        return

    tabs = st.tabs([label for label, _ in DATASETS.values()])
    for (dataset_key, (label, _)), tab in zip(DATASETS.items(), tabs, strict=True):
        with tab:
            st.subheader(label)
            try:
                frame = _load_dataset(manifest, dataset_key)
            except ReleaseError as exc:
                st.info(str(exc))
                continue
            if frame.empty:
                st.info("Chưa có kết quả tổng hợp cho mục này.")
            else:
                st.dataframe(frame, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
