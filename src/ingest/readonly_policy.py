"""Static policy checks that keep application HTTP access in the GET-only client."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterable

ALLOWED_CLIENT = Path("src/ingest/client.py")
SCANNED_ROOTS = ("src", "scripts", "notebooks")
SCANNED_SUFFIXES = {".py", ".ipynb", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
EXCLUDED_PARTS = {".git", ".venv", "__pycache__"}
EXCLUDED_FILES = {
    Path("scripts/verify_readonly.py"),
}
NETWORK_MODULES = (
    "requests",
    "httpx",
    "urllib.request",
    "urllib3",
    "aiohttp",
    "socket",
    "http.client",
    "pycurl",
    "curl_cffi",
)
FORBIDDEN_HTTP_METHODS = {"post", "put", "patch", "delete"}
DIRECT_NETWORK_CALLS = {"urlopen", "urlretrieve", "create_connection", "fetch"}
_CURL_COMMAND = re.compile(r"\bc" + r"url\b", re.IGNORECASE)
_POWERSHELL_HTTP = r"Invoke-Web" + r"Request|Invoke-Rest" + r"Method"
_FETCH_CALL = "fe" + "tch"
_ALTERNATE_HTTP = re.compile(
    r"\b(?:" + _POWERSHELL_HTTP + r")\b|"
    r"\b(?:" + _FETCH_CALL + r"|axios\.(?:get|post|put|patch|delete)|https?\.request)\s*\(",
    re.IGNORECASE,
)


def _is_network_module(module: str) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in NETWORK_MODULES)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def scan_source_text(source: str, relative_path: str | Path) -> list[str]:
    """Return read-only policy violations in one source file or notebook cell."""
    path = Path(relative_path).as_posix()
    allowed_client = path == ALLOWED_CLIENT.as_posix()
    findings: list[str] = []

    if _CURL_COMMAND.search(source):
        findings.append(f"{path}: shell network commands are prohibited; use the approved client.")
    if _ALTERNATE_HTTP.search(source):
        findings.append(f"{path}: direct HTTP client call is outside the approved client.")

    if path.lower() == "makefile" or path.endswith((".sh", ".bash", ".ps1", ".bat", ".cmd", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
        return findings

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        findings.append(f"{path}:{exc.lineno}: source could not be parsed for the read-only scan.")
        return findings

    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split(".")[0])
                if _is_network_module(alias.name) and not allowed_client:
                    findings.append(f"{path}:{node.lineno}: network module '{alias.name}' is outside the approved client.")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_network_module(module) and not allowed_client:
                findings.append(f"{path}:{node.lineno}: network module '{module}' is outside the approved client.")
            for alias in node.names:
                if alias.name in DIRECT_NETWORK_CALLS and not allowed_client:
                    findings.append(f"{path}:{node.lineno}: direct network call '{alias.name}' is outside the approved client.")
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Call):
            name = _call_name(node.func) or ""
            root = name.split(".", 1)[0]
            if root in imported_names and _is_network_module(root) and not allowed_client:
                findings.append(f"{path}:{node.lineno}: direct network call '{name}' is outside the approved client.")
            if name.split(".")[-1].lower() in FORBIDDEN_HTTP_METHODS:
                findings.append(f"{path}:{node.lineno}: forbidden HTTP method call '{name}'.")
            if name.split(".")[-1] in DIRECT_NETWORK_CALLS and not allowed_client:
                findings.append(f"{path}:{node.lineno}: direct network call '{name}' is outside the approved client.")
            if name == "__import__" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and _is_network_module(node.args[0].value):
                findings.append(f"{path}:{node.lineno}: dynamic network import is outside the approved client.")
            if name == "importlib.import_module" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and _is_network_module(node.args[0].value):
                findings.append(f"{path}:{node.lineno}: dynamic network import is outside the approved client.")

    return sorted(set(findings))


def _not_excluded(path: Path) -> bool:
    return not any(part in EXCLUDED_PARTS for part in path.parts)


def _notebook_code(source: str, path: Path) -> Iterable[tuple[str, str]]:
    try:
        notebook = json.loads(source)
    except json.JSONDecodeError as exc:
        yield f"{path.as_posix()}#notebook", f"notebook JSON is invalid: {exc.msg}"
        return
    for index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        content = cell.get("source", "")
        code = "".join(content) if isinstance(content, list) else str(content)
        yield f"{path.as_posix()}#cell-{index}", code


def scan_repository(project_root: Path) -> list[str]:
    """Scan executable project source, notebooks, and top-level launch files."""
    root = project_root.resolve()
    paths: set[Path] = set()
    for folder in SCANNED_ROOTS:
        target = root / folder
        if target.exists():
            paths.update(p for p in target.rglob("*") if p.is_file() and _not_excluded(p.relative_to(root)) and p.suffix.lower() in SCANNED_SUFFIXES)
    paths.update(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in SCANNED_SUFFIXES
    )
    makefile = root / "Makefile"
    if makefile.is_file():
        paths.add(makefile)

    findings: list[str] = []
    for file_path in sorted(paths):
        relative = file_path.relative_to(root)
        if relative in EXCLUDED_FILES:
            continue
        try:
            source = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(f"{relative.as_posix()}: source could not be read: {type(exc).__name__}.")
            continue
        if file_path.suffix.lower() == ".ipynb":
            for cell_path, cell_source in _notebook_code(source, relative):
                if cell_path.endswith("#notebook"):
                    findings.append(f"{cell_path}: {cell_source}")
                else:
                    findings.extend(scan_source_text(cell_source, cell_path))
        else:
            findings.extend(scan_source_text(source, relative))
    return sorted(set(findings))
