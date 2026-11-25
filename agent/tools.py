"""Tools the reviewer can call, behind a gateway. LAB APP: run only on the lab's own diffs.

Phase 6 fixes from the CS54 remediation plan:
  PB-06 no shell tool; every call goes through an allow-list with schema checks and a call budget;
        file tools are confined to the workspace (pattern from the CS52 tool gateway)
  PB-07 child processes get a minimal environment, so no API key is reachable from a tool
  PB-08 git is read-only: only diff, log and show, run without a shell
"""
import shlex
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
GIT_READ_ONLY = {"diff", "log", "show"}
MINIMAL_ENV = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "HOME": "/nonexistent"}
MAX_CALLS = 10


def list_files(path: str = ".") -> str:
    base = (WORKSPACE / path).resolve()
    if not base.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError(f"outside the workspace: {path}")
    return "\n".join(str(p.relative_to(WORKSPACE)) for p in sorted(base.rglob("*")) if p.is_file())


def read_file(path: str) -> str:
    target = (WORKSPACE / path).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError(f"outside the workspace: {path}")
    return target.read_text(encoding="utf-8")[:20000]


def git_read(args: str) -> str:
    parts = shlex.split(args)
    if not parts or parts[0] not in GIT_READ_ONLY:
        raise PermissionError(f"git subcommand not allowed: {parts[:1]}")
    out = subprocess.run(["git", *parts], cwd=WORKSPACE, capture_output=True, text=True, timeout=30, env=MINIMAL_ENV)
    return (out.stdout + out.stderr)[:5000]


TOOLS = {"list_files": list_files, "read_file": read_file, "git_read": git_read}

SCHEMAS = [
    {"name": "list_files", "description": "List files in the workspace",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string", "maxLength": 200}},
                      "additionalProperties": False}},
    {"name": "read_file", "description": "Read a file from the workspace",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string", "maxLength": 200}},
                      "required": ["path"], "additionalProperties": False}},
    {"name": "git_read", "description": "Read-only git: diff, log or show",
     "input_schema": {"type": "object", "properties": {"args": {"type": "string", "maxLength": 200}},
                      "required": ["args"], "additionalProperties": False}},
]
_SCHEMA = {s["name"]: s["input_schema"] for s in SCHEMAS}


class ToolGateway:
    """Allow-list, schema check, call budget and an audit trail; the model never calls a tool directly."""

    def __init__(self, max_calls: int = MAX_CALLS):
        self.max_calls, self.calls, self.audit = max_calls, 0, []

    def execute(self, name: str, args: dict) -> tuple[bool, str]:
        decision = self._check(name, args)
        if decision == "allowed":
            self.calls += 1
            try:
                result = TOOLS[name](**args)
            except (PermissionError, OSError, ValueError) as exc:
                decision, result = f"refused by tool: {exc}", f"Refused: {exc}"
        else:
            result = f"Refused: {decision}"
        self.audit.append({"tool": name, "args": args, "decision": decision})
        return decision == "allowed", result

    def _check(self, name: str, args: dict) -> str:
        if name not in TOOLS:
            return f"tool not allowed: {name}"
        if self.calls >= self.max_calls:
            return "call budget used up"
        schema = _SCHEMA[name]
        if not isinstance(args, dict) or set(args) - set(schema["properties"]):
            return "unexpected arguments"
        if any(k not in args for k in schema.get("required", [])):
            return "missing arguments"
        if any(not isinstance(v, str) or len(v) > 200 for v in args.values()):
            return "argument type or length"
        return "allowed"
