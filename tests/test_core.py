import tempfile
import unittest
import subprocess
from unittest.mock import patch

import harness.core as core
from harness.inventory import build_inventory
from harness.workspace import create_worktree, remove_worktree, workspace_status


class HarnessTests(unittest.TestCase):
  def test_plan_must_be_reapproved_after_edit(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init(); plan = core.create_plan("Demo"); core.approve_plan(plan)
            core.start_task(plan, "Demo task", "codex")
            plan.write_text(plan.read_text() + "\ncorrezione\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "non approvato"):
                core.start_task(plan, "Should fail", "codex")

  def test_conflicting_writer_is_queued(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            core.acquire_ownership(root / "a", ["harness/core.py"], "modify", "session-a")
            with self.assertRaises(core.OwnershipBusy) as caught:
                core.acquire_ownership(root / "b", ["harness/core.py"], "modify", "session-b")
            self.assertEqual(caught.exception.position, 1)
            self.assertEqual(len(core.queue_status()["queue"]), 1)
            core.release_ownership(root / "a", "session-a")
            self.assertEqual(core.queue_status()["locks"], {})

  def test_task_creates_audit_handoff_and_test_report(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Audit demo"); core.approve_plan(plan)
            task = core.start_task(plan, "Audit task", "fake")
            class Fake:
                def ask(self, prompt, on_output=None, cwd=None):
                    (root / "created-by-agent.txt").write_text("tracked", encoding="utf-8")
                    return core.Result("Implementazione completata", "fake")
            with patch.object(core, "provider", lambda name: Fake()):
                result = core.run_task(task, "fake")
            self.assertEqual(result.provider, "fake")
            self.assertTrue((task / "AUDIT.md").exists())
            self.assertIn("created-by-agent.txt", (task / "AUDIT.md").read_text(encoding="utf-8"))
            self.assertTrue((task / "HANDOFF.md").exists())
            self.assertTrue((task / "TEST-REPORT.md").exists())
            self.assertEqual(core.queue_status()["locks"], {})


  def test_parallel_runner_uses_all_tasks(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init(); tasks = []
            for index in range(2):
                plan = core.create_plan(f"Demo {index}"); core.approve_plan(plan)
                task = core.start_task(plan, f"Task {index}", "fake")
                status_path = task / "status.json"
                status = __import__("json").loads(status_path.read_text(encoding="utf-8"))
                status["paths"] = [f"isolated-{index}.txt"]
                status_path.write_text(__import__("json").dumps(status, indent=2), encoding="utf-8")
                tasks.append(task)

            class Fake:
                def ask(self, prompt, on_output=None, cwd=None): return core.Result("ok", "fake")
            with patch.object(core, "provider", lambda name: Fake()):
                results = core.run_parallel(tasks, "fake")
            self.assertEqual(len(results), 2)
            self.assertTrue(all(value == "fake" for value in results.values()))

  def test_error_is_persisted_in_catalog_and_jsonl(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Error demo"); core.approve_plan(plan)
            task = core.start_task(plan, "Error task", "fake")
            core.record_error(task, RuntimeError("errore di prova"), "test")
            self.assertIn("errore di prova", (core.STATE / "ERRORS.md").read_text(encoding="utf-8"))
            record = __import__("json").loads((core.STATE / "errors.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["type"], "RuntimeError")
            self.assertEqual(record["phase"], "test")

  def test_working_directory_is_used_for_tests(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            (root / "project").mkdir()
            (root / "project" / "marker.txt").write_text("ok", encoding="utf-8")
            plan = core.create_plan("Cwd demo"); core.approve_plan(plan)
            task = core.start_task(plan, "Cwd task", "fake", "python -c \"from pathlib import Path; raise SystemExit(0 if Path('marker.txt').exists() else 1)\"", "project")
            result = core.run_tests(task)
            self.assertEqual(result["status"], "passed")

  def test_read_only_task_rejects_workspace_changes(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Permission demo"); core.approve_plan(plan)
            task = core.start_task(plan, "Read-only task", "fake")
            status_path = task / "status.json"
            status = __import__("json").loads(status_path.read_text(encoding="utf-8")); status["permission"] = "read-only"; status["role"] = "architect"
            status_path.write_text(__import__("json").dumps(status, indent=2), encoding="utf-8")
            class Fake:
                def ask(self, prompt, on_output=None, cwd=None):
                    (root / "unauthorized.txt").write_text("blocked", encoding="utf-8")
                    return core.Result("bad", "fake")
            with patch.object(core, "provider", lambda name: Fake()):
                with self.assertRaises(PermissionError):
                    core.run_task(task, "fake")
            self.assertEqual(__import__("json").loads(status_path.read_text(encoding="utf-8"))["status"], "failed")

  def test_inventory_is_deterministic_and_does_not_read_secrets(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        (root / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n@app.route('/health')\ndef health(): return 'ok'\n", encoding="utf-8")
        (root / ".env").write_text("TOKEN=do-not-export", encoding="utf-8")
        inventory = build_inventory(root)
        app = next(item for item in inventory["files"] if item["path"] == "app.py")
        env = next(item for item in inventory["files"] if item["path"] == ".env")
        self.assertEqual(app["routes"], ["/health"])
        self.assertEqual(env["sensitivity"], "secret")
        self.assertEqual(env["access"], "denied")
        self.assertNotIn("sha256", env)
        self.assertNotIn("TOKEN=", str(inventory))

  def test_manifest_is_proposed_and_must_be_approved(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            (root / "app.py").write_text("print('ok')", encoding="utf-8")
            plan = core.create_plan("Manifest demo"); plan.write_text(plan.read_text(encoding="utf-8") + "\n## File coinvolti\n- `app.py`\n", encoding="utf-8"); core.approve_plan(plan)
            task = core.start_task(plan, "Manifest task", "fake")
            manifest = core.propose_manifest(task)
            payload = __import__("json").loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "draft")
            self.assertIn("app.py", payload["write"])
            with self.assertRaisesRegex(RuntimeError, "Manifest sandbox"):
                core.run_task(task, "fake")
            digest = core.approve_manifest(task)
            self.assertEqual(len(digest), 64)
            core.ensure_manifest_approved(task)

  def test_pipeline_runs_after_manifest_gate(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Pipeline demo"); core.approve_plan(plan)
            class Fake:
                def ask(self, prompt, on_output=None, cwd=None): return core.Result("pipeline ok", "fake")
            with patch.object(core, "provider", lambda name: Fake()), patch("builtins.input", return_value=""):
                task = core.run_pipeline(plan, "Pipeline task", "fake", "python -c \"raise SystemExit(0)\"", ".")
            status = __import__("json").loads((task / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "completed")
            self.assertTrue((task / "SANDBOX-MANIFEST.approved.json").exists())

  def test_plan_complexity_selects_proportional_workflow(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Complexity demo")
            plan.write_text(plan.read_text(encoding="utf-8").replace("- Complessità: C1", "- Complessità: C4"), encoding="utf-8")
            core.approve_plan(plan)
            task = core.start_task(plan, "Complexity task", "fake")
            self.assertEqual(core.plan_complexity(task)["workflow"], "architecture-implementation-review")

  def test_manifest_approval_requires_declared_complexity(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Legacy complexity demo")
            plan.write_text(plan.read_text(encoding="utf-8").replace("- Complessità: C1\n- Workflow proposto: single-agent\n- Motivazione: \n- Rischio: low\n", ""), encoding="utf-8")
            core.approve_plan(plan)
            task = core.start_task(plan, "Legacy complexity task", "fake")
            core.propose_manifest(task)
            with self.assertRaisesRegex(RuntimeError, "Complessità non dichiarata"):
                core.approve_manifest(task)

  def test_manifest_separates_read_write_and_create_paths(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            (root / "app.py").write_text("print('ok')", encoding="utf-8")
            plan = core.create_plan("Scope demo")
            plan.write_text(plan.read_text(encoding="utf-8") + "\n## Contesto\n- `app.py`\n\n## File coinvolti\n- `app.py`\n- `templates/new.html`\n", encoding="utf-8")
            core.approve_plan(plan)
            task = core.start_task(plan, "Scope task", "fake")
            manifest = __import__("json").loads(core.propose_manifest(task).read_text(encoding="utf-8"))
            self.assertEqual(manifest["read"], ["app.py"])
            self.assertEqual(manifest["write"], ["app.py"])
            self.assertEqual(manifest["create"], ["templates/new.html"])

  def test_git_worktree_lifecycle_is_isolated_and_reversible(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=root, check=True)
        (root / "app.py").write_text("print('base')", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        task = root / "tasks" / "demo"; task.mkdir(parents=True)
        state = root / ".coding-harness"; state.mkdir()
        worktree = create_worktree(root, task, state)
        self.assertTrue((worktree / "app.py").exists())
        self.assertEqual(workspace_status(task)["mode"], "git-worktree")
        (worktree / "app.py").write_text("print('isolated')", encoding="utf-8")
        self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "print('base')")
        remove_worktree(root, task, state, force=True)
        self.assertFalse(worktree.exists())

  def test_isolated_pipeline_runs_agent_in_worktree(self):
    with tempfile.TemporaryDirectory() as directory:
        root = __import__("pathlib").Path(directory)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=root, check=True)
        (root / "seed.txt").write_text("base", encoding="utf-8")
        subprocess.run(["git", "add", "seed.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        with patch.object(core, "ROOT", root), patch.object(core, "STATE", root / ".coding-harness"), patch.object(core, "TASKS", root / "tasks"):
            core.init()
            plan = core.create_plan("Isolated pipeline")
            plan.write_text(plan.read_text(encoding="utf-8") + "\n## File coinvolti\n- `isolated-output.txt`\n", encoding="utf-8")
            core.approve_plan(plan)
            class Fake:
                def ask(self, prompt, on_output=None, cwd=None):
                    __import__("pathlib").Path(cwd, "isolated-output.txt").write_text("worktree", encoding="utf-8")
                    return core.Result("isolated ok", "fake")
            with patch.object(core, "provider", lambda name: Fake()), patch("builtins.input", return_value=""):
                task = core.run_pipeline(plan, "Isolated pipeline task", "fake", "python -c \"raise SystemExit(0)\"", ".", isolated=True)
            metadata = __import__("json").loads((task / "workspace.json").read_text(encoding="utf-8"))
            self.assertFalse((root / "isolated-output.txt").exists())
            self.assertTrue((__import__("pathlib").Path(metadata["root"]) / "isolated-output.txt").exists())
            self.assertEqual(__import__("json").loads((task / "status.json").read_text(encoding="utf-8"))["status"], "completed")
            remove_worktree(root, task, root / ".coding-harness", force=True)


if __name__ == "__main__":
    unittest.main()
