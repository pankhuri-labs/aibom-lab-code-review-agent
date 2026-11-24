"""Tools the reviewer can call. DELIBERATELY OVER-PRIVILEGED for the lab (AT-06, AT-07, AT-08)."""
import os
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"


def list_files(path: str = ".") -> str:
    base = WORKSPACE / path
    return "\n".join(str(p.relative_to(WORKSPACE)) for p in sorted(base.rglob("*")) if p.is_file())


def read_file(path: str) -> str:
    # Weakness: no path confinement; "../" reaches outside the workspace.
    return (WORKSPACE / path).read_text(encoding="utf-8")[:20000]


def run_shell(command: str) -> str:
    # Weakness AT-06: any shell command, no allow-list, shell=True.
    # Weakness AT-07: the child process inherits the full environment, including API keys.
    out = subprocess.run(command, shell=True, cwd=WORKSPACE, capture_output=True, text=True,
                         timeout=30, env=dict(os.environ))
    return (out.stdout + out.stderr)[:5000]


def git(args: str) -> str:
    # Weakness AT-08: any git subcommand, including push, with whatever credentials the host has.
    out = subprocess.run(f"git {args}", shell=True, cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    return (out.stdout + out.stderr)[:5000]


TOOLS = {"list_files": list_files, "read_file": read_file, "run_shell": run_shell, "git": git}

SCHEMAS = [
    {"name": "list_files", "description": "List files in the workspace",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    {"name": "read_file", "description": "Read a file from the workspace",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "run_shell", "description": "Run a shell command in the workspace",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "git", "description": "Run a git command in the workspace",
     "input_schema": {"type": "object", "properties": {"args": {"type": "string"}}, "required": ["args"]}},
]
