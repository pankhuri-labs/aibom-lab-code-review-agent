# Known weaknesses (planted on purpose)

This app is a target for the [CS54 AI-BOM security lab](https://github.com/pankhuri-labs/CaseStudies/tree/main/CS54-AI-BOM-and-AI-Security-Posture-Lab). IDs match the CS54 [threat model](https://github.com/pankhuri-labs/CaseStudies/blob/main/CS54-AI-BOM-and-AI-Security-Posture-Lab/docs/threat-model.md). The [CS52 lab](https://github.com/pankhuri-labs/CaseStudies/tree/main/CS52-Agentic-AppSec-PR-Review-Crew-Lab) shows the controls; this repo starts without them on purpose. Attack tests that prove each one are in `tests/test_attacks.py` (phase 3): they assert the safe behaviour and are marked as expected failures while the weakness is present. Fixes arrive in phase 6, which removes the markers.

| ID | Weakness | Where | OWASP |
| --- | --- | --- | --- |
| AT-06 | A note hidden in a PR diff can make the agent run a shell command: no tool allow-list, `shell=True`, diff text treated as instructions | `agent/tools.py` `run_shell()`, `agent/run_review.py`, `workspace/prs/pr-001-hidden-note.diff` | LLM01, LLM06; ASI01, ASI02, ASI05 |
| AT-07 | Shell commands inherit the full process environment, so an injected command can read `ANTHROPIC_API_KEY` | `agent/tools.py` `run_shell()` | LLM02; ASI03 |
| AT-08 | The `git` tool accepts any subcommand, including push, and the intended token has repository write scope | `agent/tools.py` `git()`, `aibom.yaml` | LLM06; ASI03 |
| (extra) | `read_file` has no path confinement | `agent/tools.py` `read_file()` | LLM06; ASI02 |
