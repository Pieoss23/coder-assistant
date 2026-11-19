from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "__pycache__", ".coding-harness", "tasks", "instance", ".test-tmp"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
SECRET_MARKERS = ("secret", "password", "passwd", "token", "credential", "private", "apikey", "api_key")


def _sensitivity(path: Path) -> str:
    name = path.name.lower()
    if name in SECRET_NAMES or any(marker in name for marker in SECRET_MARKERS):
        return "secret"
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db", ".pem", ".key"}:
        return "sensitive"
    return "public"


def _type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {".py": "python", ".html": "html", ".jinja": "jinja2", ".jinja2": "jinja2", ".css": "css", ".js": "javascript", ".json": "json", ".md": "markdown", ".toml": "toml", ".yml": "yaml", ".yaml": "yaml"}.get(suffix, suffix[1:] or "file")


def _python_metadata(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"imports": [], "routes": []}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return result
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in {"route", "get", "post", "put", "patch", "delete"} and decorator.args:
                    value = decorator.args[0]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        result["routes"].append(value.value)
    result["imports"] = sorted(imports)
    result["routes"] = sorted(set(result["routes"]))
    return result


def _template_metadata(text: str) -> dict[str, Any]:
    references = {value for value in re.findall(r"(?:href|src)=[\"']([^\"']+)[\"']", text, flags=re.IGNORECASE) if not value.startswith("{{")}
    extends = re.findall(r"\{%\s*extends\s+[\"']([^\"']+)[\"']", text)
    includes = re.findall(r"\{%\s*include\s+[\"']([^\"']+)[\"']", text)
    references.update(extends)
    references.update(includes)
    return {"references": sorted(references)}


def build_inventory(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    extensions: dict[str, int] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        sensitivity = _sensitivity(path)
        item: dict[str, Any] = {"path": relative, "type": _type(path), "sensitivity": sensitivity}
        if sensitivity == "secret":
            item["access"] = "denied"
        else:
            content = path.read_bytes()
            item.update({"size": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        extensions[path.suffix.lower() or "[none]"] = extensions.get(path.suffix.lower() or "[none]", 0) + 1
        if item["sensitivity"] != "secret":
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                text = ""
            if item["type"] == "python":
                item.update(_python_metadata(text))
            elif item["type"] in {"html", "jinja2"}:
                item.update(_template_metadata(text))
        files.append(item)
    return {"schema": "coding-harness.inventory.v1", "generated_at": datetime.now().astimezone().isoformat(), "root": str(root), "file_count": len(files), "extensions": dict(sorted(extensions.items())), "files": files}


def write_inventory(root: Path, destination: Path | None = None) -> tuple[Path, Path]:
    destination = destination or root / ".coding-harness" / "inventory"
    destination.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(root)
    json_path = destination / "project-inventory.json"
    markdown_path = destination / "project-inventory.md"
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Project inventory", "", f"- File analizzati: `{inventory['file_count']}`", f"- Generato: `{inventory['generated_at']}`", "", "## Estensioni", ""]
    lines.extend(f"- `{extension}`: {count}" for extension, count in inventory["extensions"].items())
    lines.extend(["", "## File", "", "| Path | Tipo | Sensibilità | Dimensione | Metadati |", "|---|---|---|---:|---|"])
    for item in inventory["files"]:
        metadata = []
        if item.get("imports"):
            metadata.append("imports=" + ", ".join(item["imports"]))
        if item.get("routes"):
            metadata.append("routes=" + ", ".join(item["routes"]))
        if item.get("references"):
            metadata.append("refs=" + ", ".join(item["references"]))
        size = item.get("size", "redacted")
        lines.append(f"| `{item['path']}` | `{item['type']}` | `{item['sensitivity']}` | {size} | {'; '.join(metadata)} |")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
