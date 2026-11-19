from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import ROOT, STATE, TASKS, add_subtask, approve_manifest, approve_plan, build_prompt, create_plan, dispatch_queue, init, propose_manifest, queue_status, recover_ownership, run_parallel, run_pipeline, run_subtask, run_task, save_chat_output, start_task
from .inventory import write_inventory
from .workspace import create_worktree, remove_worktree, workspace_status


def main() -> None:
    parser = argparse.ArgumentParser(prog="coding-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    inv = sub.add_parser("inventory"); inv.add_argument("--output", type=Path)
    man = sub.add_parser("manifest"); ms = man.add_subparsers(dest="action", required=True)
    mp = ms.add_parser("propose"); mp.add_argument("task", type=Path)
    ma = ms.add_parser("approve"); ma.add_argument("task", type=Path)
    ws = sub.add_parser("workspace"); wss = ws.add_subparsers(dest="action", required=True)
    wsc = wss.add_parser("create"); wsc.add_argument("task", type=Path); wsc.add_argument("--ref", default="HEAD")
    wsr = wss.add_parser("remove"); wsr.add_argument("task", type=Path); wsr.add_argument("--force", action="store_true")
    wsshow = wss.add_parser("status"); wsshow.add_argument("task", type=Path)
    p = sub.add_parser("plan"); ps = p.add_subparsers(dest="action", required=True)
    c = ps.add_parser("create"); c.add_argument("title")
    a = ps.add_parser("approve"); a.add_argument("file", type=Path)
    t = sub.add_parser("task"); ts = t.add_subparsers(dest="action", required=True)
    s = ts.add_parser("start"); s.add_argument("plan", type=Path); s.add_argument("title"); s.add_argument("--provider"); s.add_argument("--test-command"); s.add_argument("--working-directory")
    r = ts.add_parser("run"); r.add_argument("task", type=Path); r.add_argument("--provider")
    pl = ts.add_parser("pipeline"); pl.add_argument("plan", type=Path); pl.add_argument("title"); pl.add_argument("--provider"); pl.add_argument("--test-command"); pl.add_argument("--working-directory"); pl.add_argument("--isolated", action="store_true")
    rp = ts.add_parser("run-parallel"); rp.add_argument("tasks", nargs="+", type=Path); rp.add_argument("--provider")
    pr = ts.add_parser("prompt"); pr.add_argument("task", type=Path)
    i = ts.add_parser("import-chat"); i.add_argument("task", type=Path); i.add_argument("output", type=Path)
    st = ts.add_parser("add-subtask"); st.add_argument("task", type=Path); st.add_argument("title"); st.add_argument("--description", default=""); st.add_argument("--role", default="developer"); st.add_argument("--provider"); st.add_argument("--path", dest="paths", action="append", default=[]); st.add_argument("--priority", type=int, default=0); st.add_argument("--depends-on", dest="depends_on", action="append", default=[])
    rs = ts.add_parser("run-subtask"); rs.add_argument("subtask", type=Path); rs.add_argument("--provider")
    m = sub.add_parser("memory"); ms = m.add_subparsers(dest="action", required=True)
    u = ms.add_parser("append"); u.add_argument("file", choices=["memory", "decisions"]); u.add_argument("text")
    q = sub.add_parser("queue"); qs = q.add_subparsers(dest="action", required=True)
    qs.add_parser("status")
    qs.add_parser("recover")
    d = qs.add_parser("dispatch"); d.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "init": init(); print(f"Harness inizializzato in {STATE}")
    elif args.command == "inventory":
        json_path, markdown_path = write_inventory(ROOT, args.output)
        print(json.dumps({"json": str(json_path), "markdown": str(markdown_path)}, indent=2))
    elif args.command == "manifest" and args.action == "propose": print(propose_manifest(args.task))
    elif args.command == "manifest" and args.action == "approve": print(f"Approvato: {approve_manifest(args.task)}")
    elif args.command == "workspace" and args.action == "create": print(create_worktree(ROOT, args.task, STATE, args.ref))
    elif args.command == "workspace" and args.action == "remove": remove_worktree(ROOT, args.task, STATE, args.force); print("Worktree rimosso")
    elif args.command == "workspace" and args.action == "status": print(json.dumps(workspace_status(args.task), indent=2))
    elif args.command == "plan" and args.action == "create": print(create_plan(args.title))
    elif args.command == "plan" and args.action == "approve": print(f"Approvato: {approve_plan(args.file)}")
    elif args.command == "task" and args.action == "start": print(start_task(args.plan, args.title, args.provider, args.test_command, args.working_directory))
    elif args.command == "task" and args.action == "run": print(run_task(args.task, args.provider).provider)
    elif args.command == "task" and args.action == "pipeline": print(f"Pipeline completata: {run_pipeline(args.plan, args.title, args.provider, args.test_command, args.working_directory, isolated=args.isolated)}")
    elif args.command == "task" and args.action == "run-parallel": print(run_parallel(args.tasks, args.provider))
    elif args.command == "task" and args.action == "prompt":
        prompt = build_prompt(args.task)
        (args.task / "AGENT_PROMPT.md").write_text(prompt, encoding="utf-8")
        print(args.task / "AGENT_PROMPT.md")
    elif args.command == "task" and args.action == "import-chat":
        save_chat_output(args.task, args.output); print(args.task / "chat-response.md")
    elif args.command == "task" and args.action == "add-subtask":
        child = add_subtask(args.task, args.title, args.description, args.role, args.provider)
        if args.paths:
            status_path = child / "status.json"
            status = json.loads(status_path.read_text(encoding="utf-8")); status["paths"] = args.paths; status["priority"] = args.priority; status["depends_on"] = args.depends_on
            status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(child)
    elif args.command == "task" and args.action == "run-subtask":
        print(run_subtask(args.subtask, args.provider).provider)
    elif args.command == "memory" and args.action == "append":
        path = STATE / ("memory.md" if args.file == "memory" else "decisions.md")
        with path.open("a", encoding="utf-8") as f: f.write(f"\n- {args.text}\n")
        print(path)
    elif args.command == "queue" and args.action == "status":
        print(json.dumps(queue_status(), indent=2, ensure_ascii=False))
    elif args.command == "queue" and args.action == "recover":
        print(json.dumps(recover_ownership(), indent=2, ensure_ascii=False))
    elif args.command == "queue" and args.action == "dispatch":
        print(json.dumps(dispatch_queue(args.limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
