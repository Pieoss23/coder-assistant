from __future__ import annotations

import hashlib
import fnmatch
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .inventory import build_inventory


ROOT = Path.cwd()
STATE = ROOT / ".coding-harness"
TASKS = ROOT / "tasks"
SLUG_MAX_LENGTH = 50
OWNERSHIP_LOCK = threading.RLock()


def load_dotenv() -> None:
    """Carica il .env locale senza dipendenze e senza sovrascrivere env esistenti."""
    dotenv = ROOT / ".env"
    if not dotenv.exists():
        return
    for raw in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def now() -> str:
    timezone_name = "Europe/Rome"
    config_path = STATE / "config.json"
    if config_path.exists():
        try:
            timezone_name = json.loads(config_path.read_text(encoding="utf-8")).get("timezone", timezone_name)
        except (OSError, json.JSONDecodeError):
            pass
    try:
        return datetime.now(ZoneInfo(timezone_name)).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def local_stamp() -> str:
    return datetime.fromisoformat(now()).strftime("%Y%m%d-%H%M%S")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_plan(path: Path) -> Path:
    if path.exists():
        return path
    candidates = [candidate for candidate in (STATE / "plans").glob("*.md") if candidate.stem.startswith(path.stem) or path.stem.startswith(candidate.stem)]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"Piano non trovato: {path}")
    raise RuntimeError("Percorso piano ambiguo: " + ", ".join(str(candidate) for candidate in candidates))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:SLUG_MAX_LENGTH]


def event(task: Path, kind: str, **data: Any) -> None:
    record = {"at": now(), "kind": kind, **data}
    with (task / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_error(task: Path, error: Exception, phase: str) -> None:
    """Conserva gli errori in forma strutturata e in un catalogo leggibile."""
    message = str(error).replace("\n", " ")
    fingerprint = hashlib.sha256(f"{type(error).__name__}:{message}".encode("utf-8")).hexdigest()[:16]
    status = {}
    status_path = task / "status.json"
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8-sig"))
    record = {"at": now(), "fingerprint": fingerprint, "type": type(error).__name__, "message": message, "phase": phase, "task": str(task), "session_id": status.get("session_id"), "provider": status.get("provider"), "role": status.get("role")}
    errors_path = STATE / "errors.jsonl"
    with errors_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    catalog = STATE / "ERRORS.md"
    if not catalog.exists():
        catalog.write_text("# Error catalog\n\nGli errori sono persistenti e vanno trasformati in test, fix o workaround documentati.\n\n", encoding="utf-8")
    with catalog.open("a", encoding="utf-8") as stream:
        stream.write(f"\n## {fingerprint} — {type(error).__name__}\n\n- Data: {record['at']}\n- Fase: `{phase}`\n- Task: `{task}`\n- Provider: `{record.get('provider') or 'n/a'}`\n- Messaggio: {message}\n- Stato: open\n")
    event(task, "error_recorded", fingerprint=fingerprint, phase=phase, error_type=type(error).__name__)


def session_id() -> str:
    return f"sess-{datetime.fromisoformat(now()).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:10]}"


def workspace_snapshot() -> dict[str, str]:
    ignored = {".coding-harness", "tasks", ".git", ".venv", "__pycache__", "node_modules"}
    result = {}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        try:
            result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return result


def write_audit(task: Path, before: dict[str, str], after: dict[str, str]) -> None:
    created = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    status = json.loads((task / "status.json").read_text(encoding="utf-8-sig"))
    def entries(values: list[str]) -> list[str]:
        return [f"- `{value}`" for value in values] or ["- Nessuno"]
    lines = ["# Audit workspace", "", f"- Sessione: `{status.get('session_id', 'unknown')}`", "", "## File creati", *entries(created), "", "## File modificati", *entries(modified), "", "## File eliminati", *entries(deleted)]
    (task / "AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def lock_path() -> Path:
    path = STATE / "ownership.json"
    if not path.exists():
        path.write_text(json.dumps({"locks": {}}, indent=2), encoding="utf-8")
    return path


def acquire_ownership(task: Path, paths: list[str], permission: str, sid: str) -> None:
    if permission == "read-only":
        return
    with OWNERSHIP_LOCK:
        path = lock_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        locks = payload.setdefault("locks", {})
        ttl = int(load_config().get("ownership_ttl_seconds", 3600))
        current_time = datetime.fromisoformat(now())
        locks = {key: value for key, value in locks.items() if (current_time - datetime.fromisoformat(value["acquired_at"])).total_seconds() < ttl}
        payload["locks"] = locks
        requested = paths or ["*"]
        conflicts = []
        for requested_path in requested:
            for owned_path, owner in locks.items():
                if requested_path == "*" or owned_path == "*" or requested_path == owned_path:
                    if owner.get("session_id") != sid:
                        conflicts.append({"path": owned_path, "owner": owner})
        if conflicts:
            queue = payload.setdefault("queue", [])
            if not any(item.get("session_id") == sid for item in queue):
                queue.append({"session_id": sid, "task": str(task), "paths": requested, "priority": 0, "enqueued_at": now(), "conflicts": conflicts})
            position = next(index + 1 for index, item in enumerate(queue) if item.get("session_id") == sid)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            raise OwnershipBusy(position)
        for requested_path in requested:
            locks[requested_path] = {"session_id": sid, "task": str(task), "acquired_at": now()}
        payload["queue"] = [item for item in payload.get("queue", []) if item.get("session_id") != sid]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def refresh_ownership(sid: str) -> None:
    with OWNERSHIP_LOCK:
        path = lock_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        for owner in payload.get("locks", {}).values():
            if owner.get("session_id") == sid:
                owner["heartbeat_at"] = now()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def release_ownership(task: Path, sid: str) -> None:
    with OWNERSHIP_LOCK:
        path = lock_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["locks"] = {key: value for key, value in payload.get("locks", {}).items() if value.get("session_id") != sid}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def queue_status() -> dict[str, Any]:
    payload = json.loads(lock_path().read_text(encoding="utf-8"))
    queue = sorted(payload.get("queue", []), key=lambda item: (-int(item.get("priority", 0)), item.get("enqueued_at", "")))
    return {"locks": payload.get("locks", {}), "queue": queue}


def dependencies_ready(task: Path) -> bool:
    status = json.loads((task / "status.json").read_text(encoding="utf-8"))
    for dependency in status.get("depends_on", []):
        dependency_status = Path(dependency) / "status.json"
        if not dependency_status.exists() or json.loads(dependency_status.read_text(encoding="utf-8")).get("status") != "completed":
            return False
    return True


def dispatch_queue(limit: int | None = None) -> dict[str, str]:
    results: dict[str, str] = {}
    for item in queue_status()["queue"][:limit]:
        task = Path(item["task"])
        if not task.exists() or not dependencies_ready(task):
            results[str(task)] = "waiting-dependency"
            continue
        try:
            results[str(task)] = run_subtask(task, None).provider
        except OwnershipBusy:
            results[str(task)] = "waiting-ownership"
        except Exception as exc:
            results[str(task)] = f"ERROR: {exc}"
    return results


def recover_ownership() -> dict[str, Any]:
    path = lock_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    ttl = int(load_config().get("ownership_ttl_seconds", 3600))
    current_time = datetime.fromisoformat(now())
    before = len(payload.get("locks", {}))
    payload["locks"] = {key: value for key, value in payload.get("locks", {}).items() if (current_time - datetime.fromisoformat(value["acquired_at"])).total_seconds() < ttl}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"removed_locks": before - len(payload["locks"]), **queue_status()}


def write_handoff(task: Path, status: dict[str, Any], tests: dict[str, Any] | None = None) -> None:
    (task / "HANDOFF.md").write_text("# Handoff agente\n\n"
        f"- **Sessione:** `{status.get('session_id', 'unknown')}`\n- **Identità:** {status.get('identity', 'unknown')}\n"
        f"- **Provider:** `{status.get('provider', 'unknown')}`\n- **Ruolo:** `{status.get('role', 'unknown')}`\n"
        f"- **Permesso:** `{status.get('permission', 'unknown')}`\n- **Stato:** `{status.get('status')}`\n\n"
        "## Artefatti\n\n- `agent-output.md` — risposta dell’agente\n- `AUDIT.md` — file creati/modificati/eliminati\n- `TEST-REPORT.md` — risultato test\n\n"
        f"## Test\n\n```json\n{json.dumps(tests or status.get('tests', {}), indent=2, ensure_ascii=False)}\n```\n", encoding="utf-8")


def announce(task: Path, status: dict[str, Any], phase: str) -> None:
    print(f"\n[{status.get('session_id', '?')}] {status.get('identity', status.get('provider', '?'))} | {phase}", flush=True)
    print(f"  workspace : {ROOT}", flush=True)
    print(f"  task      : {task}", flush=True)
    print(f"  destinazione: {ROOT}", flush=True)
    print(f"  permesso  : {status.get('permission', 'unknown')} | paths: {', '.join(status.get('paths', ['*']))}", flush=True)


def stream_line(task: Path, text: str) -> None:
    rendered = f"[{task.name}] {text}"
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe = rendered.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(safe, end="" if text.endswith("\n") else "\n", flush=True)


def cli_event_text(raw: str, json_events: bool) -> str:
    if not json_events:
        return raw
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    item = payload.get("item", {})
    text = item.get("text") or payload.get("message") or payload.get("delta", {}).get("text")
    if text:
        return str(text)
    event_type = payload.get("type")
    if event_type in {"turn.started", "turn.completed", "item.started", "item.completed"}:
        return f"[{event_type}]\n"
    return ""


def test_command(task: Path | None = None) -> str | None:
    configured = None
    if task and (task / "status.json").exists():
        configured = json.loads((task / "status.json").read_text(encoding="utf-8-sig")).get("test_command")
    configured = configured or load_config().get("test_command")
    if configured:
        return configured
    if (ROOT / "package.json").exists():
        return "npm test"
    if (ROOT / "pytest.ini").exists():
        return "python -m pytest"
    if (ROOT / "tests").exists():
        return "python -m unittest discover -s tests -v"
    return None


def terminal_command(command: str) -> list[str]:
    """Converte un comando shell in argv coerente con il terminale configurato."""
    terminal = load_config().get("terminal", {})
    shell = str(terminal.get("shell", "powershell" if os.name == "nt" else "sh")).lower()
    if shell in {"powershell", "pwsh"}:
        executable = str(terminal.get("executable", "powershell.exe" if shell == "powershell" else "pwsh"))
        return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
    if shell == "cmd":
        executable = str(terminal.get("executable", "cmd.exe"))
        return [executable, "/d", "/s", "/c", command]
    executable = str(terminal.get("executable", shell))
    return [executable, "-lc", command]


def task_working_directory(task: Path) -> Path:
    status = json.loads((task / "status.json").read_text(encoding="utf-8-sig")) if (task / "status.json").exists() else {}
    configured = status.get("working_directory") or load_config().get("working_directory") or "."
    candidate = (ROOT / configured).resolve() if not Path(configured).is_absolute() else Path(configured).resolve()
    if candidate != ROOT.resolve() and ROOT.resolve() not in candidate.parents:
        raise ValueError(f"working_directory fuori dal workspace: {configured}")
    if not candidate.exists() or not candidate.is_dir():
        raise FileNotFoundError(f"working_directory non trovato: {candidate}")
    return candidate


def run_tests(task: Path) -> dict[str, Any]:
    """Esegue la suite configurata e lascia sempre un report nel task."""
    command = test_command(task)
    report = task / "TEST-REPORT.md"
    if not command:
        result = {"status": "not-configured", "command": None, "returncode": None}
        report.write_text("# Test report\n\nTest automatici non configurati. Impostare `test_command` in `.coding-harness/config.json`.\n", encoding="utf-8")
        event(task, "tests_skipped", reason="not-configured")
        return result
    try:
        argv = terminal_command(command)
        cwd = task_working_directory(task)
        completed = subprocess.run(argv, cwd=cwd, shell=False, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=1800)
        status = "passed" if completed.returncode == 0 else "failed"
        result = {"status": status, "command": command, "working_directory": str(cwd), "terminal": load_config().get("terminal", {}).get("shell"), "returncode": completed.returncode}
        if status == "failed":
            record_error(task, RuntimeError(f"suite fallita con return code {completed.returncode}"), "tests-failed")
        report.write_text("# Test report\n\n"
            f"- **Esito:** {status}\n- **Comando:** `{command}`\n- **Return code:** `{completed.returncode}`\n\n"
            "## Output\n\n```text\n" + (completed.stdout + "\n" + completed.stderr).strip() + "\n```\n", encoding="utf-8")
        event(task, "tests_completed", **result)
        return result
    except subprocess.TimeoutExpired as exc:
        record_error(task, exc, "tests-timeout")
        report.write_text(f"# Test report\n\n- **Esito:** timeout\n- **Comando:** `{command}`\n\n## Output\n\n```text\n{exc}\n```\n", encoding="utf-8")
        event(task, "tests_timeout", command=command)
        return {"status": "timeout", "command": command, "returncode": None}
    except Exception as exc:
        record_error(task, exc, "tests")
        report.write_text(f"# Test report\n\n- **Esito:** error\n- **Comando:** `{command}`\n- **Errore:** {exc}\n", encoding="utf-8")
        event(task, "tests_error", command=command, error=str(exc))
        return {"status": "error", "command": command, "returncode": None}


def load_config() -> dict[str, Any]:
    load_dotenv()
    path = STATE / "config.json"
    if not path.exists():
        return {"default_provider": "openrouter", "providers": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def read_context() -> str:
    parts = []
    for name in ("SYSTEM_PROMPT.md", "PROJECT_RULES.md", "memory.md", "decisions.md", "ERRORS.md"):
        path = STATE / name
        if path.exists():
            parts.append(f"\n--- {name} ---\n{path.read_text(encoding='utf-8')}")
    return "".join(parts)


def project_agent(provider_name: str | None, role: str | None) -> dict[str, Any]:
    config = load_config()
    agents = config.get("agents", {})
    profile = dict(agents.get(role or "developer", {}))
    profile.setdefault("role", role or "developer")
    profile.setdefault("provider", provider_name or config.get("default_provider", "openrouter"))
    profile.setdefault("identity", f"{profile['role']} del progetto {config.get('project_name', 'current-project')}")
    profile.setdefault("permission", "read-only")
    return profile


def shared_markdown(task: Path) -> str:
    """Condivide in modo esplicito i Markdown del task padre e dei fratelli."""
    parent = task.parent.parent if task.parent.name == "subtasks" else task
    files: list[Path] = [parent / "PLAN.md"]
    if task.parent.name == "subtasks":
        files.extend(sorted(task.parent.glob("*/agent-output.md")))
        files.extend(sorted(task.parent.glob("*/TEST-REPORT.md")))
    parts = []
    for path in files:
        if path.exists() and path.resolve() != (task / "agent-output.md").resolve():
            text = path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"\n--- SHARED {path.relative_to(parent)} ---\n{text[:12000]}")
    return "".join(parts)


@dataclass
class Result:
    text: str
    provider: str


class OwnershipBusy(RuntimeError):
    def __init__(self, position: int):
        super().__init__(f"Ownership occupata: task accodato in posizione {position}")
        self.position = position


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted((set(after) ^ set(before)) | {path for path in set(before) & set(after) if before[path] != after[path]})


def validate_changes(before: dict[str, str], after: dict[str, str], paths: list[str], permission: str) -> list[str]:
    changed = changed_paths(before, after)
    if permission == "read-only":
        unauthorized = changed
    else:
        patterns = [pattern.replace("\\", "/") for pattern in (paths or ["*"])]
        unauthorized = [path for path in changed if not any(fnmatch.fnmatch(path.replace("\\", "/"), pattern) or path.replace("\\", "/").startswith(pattern.rstrip("*").rstrip("/") + "/") for pattern in patterns)]
    if unauthorized:
        raise PermissionError("Modifiche fuori permesso: " + ", ".join(unauthorized))
    return changed


def manifest_file(task: Path) -> Path:
    return task / "SANDBOX-MANIFEST.json"


def _plan_paths(task: Path, inventory: dict[str, Any]) -> list[str]:
    plan = (task / "PLAN.md").read_text(encoding="utf-8", errors="replace")
    tokens = re.findall(r"`([^`]+)`", plan)
    known = [item["path"] for item in inventory["files"]]
    selected: set[str] = set()
    for token in tokens:
        candidate = token.strip().replace("\\", "/")
        if not candidate or candidate.startswith("http") or candidate.startswith("<"):
            continue
        if candidate.endswith("/"):
            selected.update(path for path in known if path.startswith(candidate))
            selected.add(candidate + "*")
        elif candidate in known:
            selected.add(candidate)
    return sorted(selected)


def plan_complexity(task: Path) -> dict[str, str]:
    plan = (task / "PLAN.md").read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?:complexity|complessità|complessita)\s*:\s*(C[0-5])", plan, flags=re.IGNORECASE)
    declared = bool(match)
    level = match.group(1).upper() if match else "C1"
    workflows = {"C0": "single-agent", "C1": "single-agent", "C2": "single-agent-review-optional", "C3": "implementation-review", "C4": "architecture-implementation-review", "C5": "multi-agent-isolated"}
    return {"level": level, "workflow": workflows[level], "declared": declared, "source": "plan" if declared else "legacy-default"}


def propose_manifest(task: Path) -> Path:
    task = Path(task)
    if not (task / "PLAN.md").exists():
        raise FileNotFoundError(task / "PLAN.md")
    inventory = build_inventory(ROOT)
    paths = _plan_paths(task, inventory)
    sensitive = sorted(item["path"] for item in inventory["files"] if item["sensitivity"] == "secret")
    status = json.loads((task / "status.json").read_text(encoding="utf-8-sig")) if (task / "status.json").exists() else {}
    manifest = {
        "schema": "coding-harness.sandbox-manifest.v1",
        "status": "draft",
        "task": str(task),
        "plan_sha256": sha(task / "PLAN.md"),
        "complexity": plan_complexity(task),
        "inventory_generated_at": inventory["generated_at"],
        "read": paths,
        "write": paths,
        "create": [],
        "deny": [".env", "*/.env", ".coding-harness/*", "instance/*", "*.sqlite3"],
        "sensitive": sensitive,
        "commands": [status["test_command"]] if status.get("test_command") else [],
        "network": False,
        "notes": ["Bozza generata deterministicamente dall'inventory e dal piano. Verificare e approvare prima dell'esecuzione."] + ([] if plan_complexity(task)["declared"] else ["Complessità assente nel piano: aggiungere una valutazione C0-C5 prima dell'approvazione."])
    }
    path = manifest_file(task)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def approve_manifest(task: Path) -> str:
    path = manifest_file(Path(task))
    if not path.exists():
        raise FileNotFoundError(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not manifest.get("complexity", {}).get("declared", False):
        raise RuntimeError("Complessità non dichiarata nel piano: aggiungere '- Complessità: C0-C5' e rigenerare il manifest")
    manifest["status"] = "approved"
    manifest["approved_at"] = now()
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    digest = sha(path)
    (path.parent / "SANDBOX-MANIFEST.approved.json").write_text(json.dumps({"manifest": str(path), "sha256": digest, "approved_at": manifest["approved_at"]}, indent=2) + "\n", encoding="utf-8")
    return digest


def ensure_manifest_approved(task: Path) -> None:
    path = manifest_file(task)
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    approval = path.parent / "SANDBOX-MANIFEST.approved.json"
    if manifest.get("status") != "approved" or not approval.exists() or json.loads(approval.read_text(encoding="utf-8"))["sha256"] != sha(path):
        raise RuntimeError("Manifest sandbox non approvato oppure modificato dopo l'approvazione")


def manifest_write_paths(task: Path, status: dict[str, Any]) -> list[str]:
    path = manifest_file(task)
    if not path.exists():
        return status.get("paths", ["*"])
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return sorted(set(manifest.get("write", []) + manifest.get("create", [])))


class Provider:
    def __init__(self, name: str, settings: dict[str, Any]):
        self.name, self.settings = name, settings

    def ask(self, prompt: str, on_output=None) -> Result:
        if self.name == "openrouter":
            return self._openrouter(prompt, on_output)
        if self.name in {"claude", "codex", "copilot"}:
            return self._cli(prompt, on_output)
        raise ValueError(f"Provider non supportato: {self.name}")

    def _openrouter(self, prompt: str, on_output=None) -> Result:
        key = os.getenv(self.settings.get("api_key_env", "OPENROUTER_API_KEY"))
        if not key:
            raise RuntimeError("Variabile API key OpenRouter non configurata")
        streaming = self.settings.get("stream", True)
        body = json.dumps({"model": self.settings.get("model", "anthropic/claude-3.5-sonnet"),
                           "messages": [{"role": "user", "content": prompt}], "stream": streaming}).encode()
        req = urllib.request.Request(self.settings.get("base_url", "https://openrouter.ai/api/v1/chat/completions"),
            data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as response:
            if not streaming:
                payload = json.loads(response.read())
                return Result(payload["choices"][0]["message"]["content"], self.name)
            chunks = []
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                payload = json.loads(data)
                text = payload.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if text:
                    chunks.append(text)
                    if on_output:
                        on_output(text)
        return Result("".join(chunks), self.name)

    def _cli(self, prompt: str, on_output=None) -> Result:
        command = self.settings.get("command", self.name)
        default_args = ["-p", prompt] if self.name in {"claude", "copilot"} else ["exec", prompt]
        configured_args = self.settings.get("args", default_args)
        via_stdin = bool(self.settings.get("prompt_via_stdin", False))
        json_events = bool(self.settings.get("json_events", False))
        args = [str(item).replace("{prompt}", prompt) for item in configured_args]
        if not via_stdin and "{prompt}" not in " ".join(map(str, configured_args)):
            args.append(prompt)
        process = subprocess.Popen([command, *args], stdin=subprocess.PIPE if via_stdin else subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        if via_stdin and process.stdin:
            process.stdin.write(prompt)
            process.stdin.close()
        output = []
        assert process.stdout is not None
        for line in process.stdout:
            visible = cli_event_text(line, json_events)
            if visible:
                output.append(visible)
                if on_output:
                    on_output(visible)
        try:
            process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        if process.returncode:
            raise RuntimeError("".join(output).strip() or f"{self.name} ha restituito {process.returncode}")
        return Result("".join(output), self.name)


def provider(name: str | None) -> Provider:
    config = load_config()
    selected = name or config.get("default_provider", "openrouter")
    return Provider(selected, config.get("providers", {}).get(selected, {}))


def init() -> None:
    STATE.mkdir(exist_ok=True)
    TASKS.mkdir(exist_ok=True)
    defaults = {
        "SYSTEM_PROMPT.md": "# System prompt\n\nSei un senior software engineer. Prima analizza, poi modifica. Verifica ogni cambiamento.\n",
        "PROJECT_RULES.md": "# Regole del progetto\n\nDefinisci qui architettura, stack, convenzioni, vincoli e criteri di qualità. Questo file è autorevole.\n",
        "memory.md": "# Memoria persistente\n\n## Obiettivi\n\n## Vincoli e preferenze\n\n## Pattern confermati\n",
        "decisions.md": "# Decision log\n\nLe decisioni vengono aggiunte dagli agenti con motivazione e impatto.\n",
        "ERRORS.md": "# Error catalog\n\nGli errori persistono qui e devono portare a test, fix o workaround documentati.\n",
        "config.json": json.dumps({"default_provider": "openrouter", "project_name": "Nuovo progetto", "timezone": "Europe/Rome", "test_command": "python -m unittest discover -s tests -v", "agents": {
        "architect": {"identity": "Architect del progetto", "permission": "read-only"},
        "developer": {"identity": "Developer del progetto", "permission": "modify"},
        "implementer": {"identity": "Implementer del progetto", "permission": "modify"},
        "tester-reviewer": {"identity": "Tester-reviewer del progetto", "permission": "both"}}, "providers": {
        "openrouter": {"model": "anthropic/claude-3.5-sonnet", "api_key_env": "OPENROUTER_API_KEY"},
            "claude": {"command": "claude"}, "codex": {"command": "codex"},
        "copilot": {"command": "copilot"}
        }}, indent=2) + "\n"
    }
    for name, content in defaults.items():
        path = STATE / name
        if not path.exists(): path.write_text(content, encoding="utf-8")


def create_plan(title: str) -> Path:
    (STATE / "plans").mkdir(exist_ok=True)
    path = STATE / "plans" / f"{local_stamp()}-{slug(title)}.md"
    path.write_text(f"# Piano: {title}\n\n## Valutazione del task\n\n- Complessità: C1\n- Workflow proposto: single-agent\n- Motivazione: \n- Rischio: low\n\n## Obiettivo\n\n## Contesto\n\n## Attività atomiche\n\n- [ ] \n\n## File coinvolti\n\n## Criteri di accettazione\n\n## Rischi e rollback\n\n", encoding="utf-8")
    return path


def approve_plan(path: Path) -> str:
    path = resolve_plan(path)
    approval = STATE / "plans" / f"{path.stem}.approved.json"
    payload = {"plan": str(path), "sha256": sha(path), "approved_at": now()}
    approval.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload["sha256"]


def ensure_approved(path: Path) -> None:
    path = resolve_plan(path)
    approval = STATE / "plans" / f"{path.stem}.approved.json"
    if not approval.exists() or json.loads(approval.read_text(encoding="utf-8"))["sha256"] != sha(path):
        raise RuntimeError("Piano non approvato oppure modificato dopo l'approvazione")


def start_task(plan: Path, title: str, provider_name: str | None, test_command_value: str | None = None, working_directory: str | None = None) -> Path:
    plan = resolve_plan(plan)
    ensure_approved(plan)
    task = TASKS / f"{local_stamp()}-{slug(title)}"
    task.mkdir(parents=True)
    (task / "PLAN.md").write_text(plan.read_text(encoding="utf-8"), encoding="utf-8")
    (task / "AGENT_PROMPT.md").write_text(build_prompt(task), encoding="utf-8")
    (task / "TEST-REPORT.md").write_text("# Test report\n\nIn attesa dell’esecuzione del task.\n", encoding="utf-8")
    (task / "subtasks").mkdir()
    profile = project_agent(provider_name, "developer")
    (task / "status.json").write_text(json.dumps({"status":"created", "session_id":session_id(), "provider":profile["provider"], "role":profile["role"], "identity":profile["identity"], "permission":profile["permission"], "workspace_root":str(ROOT), "destination":str(ROOT), "paths":["*"], "test_command":test_command_value, "working_directory":working_directory or load_config().get("working_directory", "."), "plan_sha256":sha(plan), "created_at":now()}, indent=2), encoding="utf-8")
    event(task, "task_created", plan=str(plan), identity=profile["identity"], permission=profile["permission"])
    return task


def run_pipeline(plan: Path, title: str, provider_name: str | None, test_command_value: str | None = None, working_directory: str | None = None, interactive: bool = True) -> Path:
    """Esegue il workflow minimo con gate umano sul manifest sandbox."""
    task = start_task(plan, title, provider_name, test_command_value, working_directory)
    manifest = propose_manifest(task)
    print(f"Task creato: {task}", flush=True)
    print(f"Manifest sandbox: {manifest}", flush=True)
    if interactive:
        input("Modifica/verifica il manifest, poi premi INVIO per approvarlo e continuare (CTRL+C per fermare): ")
    approve_manifest(task)
    print("Manifest approvato. Avvio agente e test...", flush=True)
    run_task(task, provider_name)
    return task


def build_prompt(task: Path) -> str:
    """Crea il messaggio completo da usare nella chat dell'agente."""
    status = json.loads((task / "status.json").read_text(encoding="utf-8-sig")) if (task / "status.json").exists() else {}
    profile = project_agent(status.get("provider"), status.get("role"))
    permission = status.get("permission", profile["permission"])
    return read_context() + shared_markdown(task) + "\n\n" + (
        f"La tua identità per questo progetto è **{profile['identity']}**. Il tuo ruolo è **{profile['role']}**. "
        f"Il tuo permesso dichiarato è **{permission}**: rispettalo e non oltrepassarlo.\n\n"
        "Sei l'agente incaricato di questo task. Rispetta integralmente SYSTEM_PROMPT, "
        "PROJECT_RULES e memoria. Prima riepiloga il piano e le assunzioni; poi sviluppa "
        "in modo incrementale. Devi creare o aggiornare test pertinenti, eseguirli e riportare "
        "file modificati, test eseguiti, rischi e decisioni. "
        "Se una richiesta contraddice le regole, fermati e segnalalo.\n\n"
        "## Piano del task\n\n" + (task / "PLAN.md").read_text(encoding="utf-8")
    )


def save_chat_output(task: Path, output: Path) -> None:
    """Archivia la risposta copiata dalla chat e la registra nella timeline."""
    if not output.exists():
        raise FileNotFoundError(output)
    destination = task / "chat-response.md"
    destination.write_text(output.read_text(encoding="utf-8"), encoding="utf-8")
    event(task, "chat_response_imported", source=str(output))


def add_subtask(task: Path, title: str, description: str = "", role: str = "developer", provider_name: str | None = None) -> Path:
    subtasks = task / "subtasks"
    subtasks.mkdir(exist_ok=True)
    index = len(list(subtasks.iterdir())) + 1
    child = subtasks / f"{index:03d}-{slug(title)}"
    child.mkdir()
    (child / "PLAN.md").write_text(f"# Sotto-task: {title}\n\n## Ruolo\n\n{role}\n\n## Obiettivo\n\n{description}\n\n## Attività\n\n- [ ] \n\n## Criteri di accettazione\n\n", encoding="utf-8")
    (child / "TEST-REPORT.md").write_text("# Test report\n\nIn attesa dell’esecuzione del sotto-task.\n", encoding="utf-8")
    parent_status = json.loads((task / "status.json").read_text(encoding="utf-8-sig")) if (task / "status.json").exists() else {}
    profile = project_agent(provider_name, role)
    (child / "status.json").write_text(json.dumps({"status":"created", "session_id":session_id(), "parent":str(task), "role":role, "identity":profile["identity"], "permission":profile["permission"], "provider":profile["provider"], "workspace_root":str(ROOT), "destination":str(ROOT), "paths":["*"], "test_command":parent_status.get("test_command"), "working_directory":parent_status.get("working_directory", "."), "created_at":now()}, indent=2), encoding="utf-8")
    event(task, "subtask_created", subtask=str(child), identity=profile["identity"], permission=profile["permission"])
    return child


def run_subtask(task: Path, provider_name: str | None) -> Result:
    status_path = task / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    ensure_manifest_approved(task)
    scoped_paths = manifest_write_paths(task, status)
    status["status"] = "running"
    for key in ("error", "failed_at", "queue_position", "queued_at"):
        status.pop(key, None)
    sid = status.setdefault("session_id", session_id())
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    announce(task, status, "START / analisi ed esecuzione")
    before = workspace_snapshot()
    try:
        acquire_ownership(task, scoped_paths, status.get("permission", "modify"), sid)
    except OwnershipBusy as exc:
        status.update({"status": "queued", "queue_position": exc.position, "queued_at": now()})
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        raise
    role = status.get("role", "developer")
    profile = project_agent(provider_name or status.get("provider"), role)
    prompt = read_context() + shared_markdown(task) + f"\n\nLa tua identità è **{profile['identity']}**. Agisci nel ruolo di **{role}** con permesso **{profile['permission']}**. Workspace: `{ROOT}`. Destinazione: `{ROOT}`. " + "Esegui questo sotto-task nel progetto condiviso. Crea ed esegui i test pertinenti:\n\n" + (task / "PLAN.md").read_text(encoding="utf-8")
    try:
        result = provider(provider_name or status.get("provider") or load_config().get("default_provider")).ask(prompt, on_output=lambda chunk: stream_line(task, chunk))
        (task / "agent-output.md").write_text(result.text, encoding="utf-8")
        refresh_ownership(sid)
        validate_changes(before, workspace_snapshot(), scoped_paths, status.get("permission", "modify"))
        test_result = run_tests(task)
        announce(task, status, "TEST / suite automatica")
        final_status = "completed" if test_result["status"] in {"passed", "not-configured"} else "needs-review"
        status.update({"status":final_status, "provider":result.provider, "tests":test_result, "completed_at":now()})
        write_handoff(task, status, test_result)
        return result
    except Exception as exc:
        record_error(task, exc, "agent")
        status.update({"status":"failed", "error":str(exc), "failed_at":now()})
        raise
    finally:
        write_audit(task, before, workspace_snapshot())
        release_ownership(task, sid)
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def run_task(task: Path, provider_name: str | None) -> Result:
    status = json.loads((task / "status.json").read_text(encoding="utf-8-sig"))
    ensure_manifest_approved(task)
    scoped_paths = manifest_write_paths(task, status)
    status["status"] = "running"; status["started_at"] = now()
    for key in ("error", "failed_at", "queue_position", "queued_at"):
        status.pop(key, None)
    sid = status.setdefault("session_id", session_id())
    (task / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    announce(task, status, "START / analisi ed esecuzione")
    before = workspace_snapshot()
    try:
        acquire_ownership(task, scoped_paths, status.get("permission", "modify"), sid)
    except OwnershipBusy as exc:
        status.update({"status": "queued", "queue_position": exc.position, "queued_at": now()})
        (task / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        raise
    prompt = read_context() + "\n\nEsegui il piano seguente. Lavora in modo incrementale, annota decisioni e test: \n" + (task / "PLAN.md").read_text(encoding="utf-8")
    event(task, "execution_started", provider=provider_name or status["provider"])
    try:
        result = provider(provider_name or status["provider"]).ask(prompt, on_output=lambda chunk: stream_line(task, chunk))
        (task / "agent-output.md").write_text(result.text, encoding="utf-8")
        refresh_ownership(sid)
        validate_changes(before, workspace_snapshot(), scoped_paths, status.get("permission", "modify"))
        test_result = run_tests(task)
        announce(task, status, "TEST / suite automatica")
        final_status = "completed" if test_result["status"] in {"passed", "not-configured"} else "needs-review"
        status.update({"status":final_status, "tests":test_result, "completed_at":now()})
        write_handoff(task, status, test_result)
        event(task, "execution_completed", provider=result.provider)
    except Exception as exc:
        record_error(task, exc, "agent")
        status.update({"status":"failed", "error":str(exc), "failed_at":now()})
        event(task, "execution_failed", error=str(exc))
        raise
    finally:
        write_audit(task, before, workspace_snapshot())
        release_ownership(task, sid)
        (task / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    return result


def run_parallel(tasks: list[Path], provider_name: str | None) -> dict[str, str]:
    results = {}
    with ThreadPoolExecutor(max_workers=min(8, len(tasks) or 1)) as pool:
        futures = {pool.submit(run_task, task, provider_name): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try: results[str(task)] = future.result().provider
            except Exception as exc: results[str(task)] = f"ERROR: {exc}"
    return results
