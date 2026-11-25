# Known weaknesses (planted on purpose, fixed in phase 6)

This app is a target for the [CS54 AI-BOM security lab](https://github.com/pankhuri-labs/CaseStudies/tree/main/CS54-AI-BOM-and-AI-Security-Posture-Lab). IDs match the CS54 [threat model](https://github.com/pankhuri-labs/CaseStudies/blob/main/CS54-AI-BOM-and-AI-Security-Posture-Lab/docs/threat-model.md). The [CS52 lab](https://github.com/pankhuri-labs/CaseStudies/tree/main/CS52-Agentic-AppSec-PR-Review-Crew-Lab) shows the controls; this repo starts without them on purpose. Attack tests that prove each one are in `tests/test_attacks.py` (phase 3): they assert the safe behaviour and are marked as expected failures while the weakness is present. Phase 6 fixed them and removed the markers; the table below the original list shows each fix.

| ID | Weakness | Where | OWASP |
| --- | --- | --- | --- |
| AT-06 | A note hidden in a PR diff can make the agent run a shell command: no tool allow-list, `shell=True`, diff text treated as instructions | `agent/tools.py` `run_shell()`, `agent/run_review.py`, `workspace/prs/pr-001-hidden-note.diff` | LLM01, LLM06; ASI01, ASI02, ASI05 |
| AT-07 | Shell commands inherit the full process environment, so an injected command can read `ANTHROPIC_API_KEY` | `agent/tools.py` `run_shell()` | LLM02; ASI03 |
| AT-08 | The `git` tool accepts any subcommand, including push, and the intended token has repository write scope | `agent/tools.py` `git()`, `aibom.yaml` | LLM06; ASI03 |
| (extra) | `read_file` has no path confinement | `agent/tools.py` `read_file()` | LLM06; ASI02 |

## Phase 6 fixes

Each fix follows a playbook in the CS54 remediation plan. A fix counts as closed only when its attack test passes **and** the AI-BOM rescan no longer raises the signal.

| ID | Playbook | Fix | Proof |
| --- | --- | --- | --- |
| AT-06 | PB-06 | `run_shell` removed. Every call goes through `ToolGateway`: an allow-list of three read-only tools, schema and length checks, a budget of 10 calls and an audit trail. The prompt and the first message say diff text is data, not instructions. | `test_at06_hidden_note_in_diff_does_not_run_a_command`, `test_at06_gateway_refuses_tools_the_model_invents` |
| AT-07 | PB-07 | No tool inherits the process environment; `git_read` runs with a minimal environment (`PATH` and git settings only). | `test_at07_tools_cannot_read_the_model_api_key` |
| AT-08 | PB-08 | `git` replaced by `git_read`, which allows only `diff`, `log` and `show`, with list arguments and no shell. The intended token is narrowed to reading code and writing PR comments, and `aibom.yaml` now labels the agent internet-facing, because outside contributors can trigger it. | `test_at08_git_tool_refuses_push` |
| (extra) | PB-06 | `read_file` and `list_files` resolve the path and refuse anything outside `workspace/`. | `test_extra_read_file_stays_in_the_workspace` |

The fake model still tries the shell command from the hidden note; the gateway refuses it and records the refusal. With a real model, run `real-model/agent_trials.py` from CS54 to measure how often the model still tries.
