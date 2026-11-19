from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class WorkspaceError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], text=True, encoding="utf-8", errors="replace", capture_output=True)


def create_worktree(root: Path, task: Path, state: Path, ref: str = "HEAD") -> Path:
    if not (_git(root, "rev-parse", "--show-toplevel").returncode == 0):
        raise WorkspaceError("Il workspace non è una repository Git")
    worktrees = state / "worktrees"
    worktrees.mkdir(parents=True, exist_ok=True)
    destination = worktrees / task.name
    if destination.exists():
        raise WorkspaceError(f"Worktree già esistente: {destination}")
    result = _git(root, "worktree", "add", "--detach", str(destination), ref)
    if result.returncode != 0:
        raise WorkspaceError(result.stderr.strip() or "Impossibile creare il worktree")
    metadata: dict[str, Any] = {"mode": "git-worktree", "root": str(destination), "source_root": str(root), "ref": ref, "created_at": __import__("datetime").datetime.now().astimezone().isoformat()}
    (task / "workspace.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return destination


def remove_worktree(root: Path, task: Path, state: Path, force: bool = False) -> None:
    metadata_path = task / "workspace.json"
    if not metadata_path.exists():
        raise WorkspaceError(f"Nessun workspace isolato per {task}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    destination = Path(metadata["root"])
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(destination))
    result = _git(root, *args)
    if result.returncode != 0:
        raise WorkspaceError(result.stderr.strip() or "Impossibile rimuovere il worktree")
    metadata_path.unlink()


def workspace_status(task: Path) -> dict[str, Any]:
    metadata_path = task / "workspace.json"
    if not metadata_path.exists():
        return {"mode": "shared", "root": None}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["exists"] = Path(metadata["root"]).exists()
    return metadata
