# aibom-lab-code-review-agent

An AI agent that reviews pull request diffs for security problems, using read-only tools behind a gateway to read files and git history. It runs on **Claude** (hosted, Anthropic API) or **Qwen 2.5 Coder 1.5B** (local, Ollama).

> **Deliberately vulnerable lab app. Run it only on the lab's own diffs in `workspace/prs/`.** It is one of four sample apps for the [CS54 AI-BOM and AI security posture lab](https://github.com/pankhuri-labs/CaseStudies/tree/main/CS54-AI-BOM-and-AI-Security-Posture-Lab). Its planted weaknesses, and the phase 6 fixes, are listed in [KNOWN-WEAKNESSES.md](KNOWN-WEAKNESSES.md).

## What it is, in AI-BOM terms

| AI-BOM field | Value |
| --- | --- |
| Models | `claude-haiku-5-5` (hosted, Anthropic) or `qwen2.5-coder:1.5b` (local, Ollama) |
| Prompt | `prompts/system.txt` |
| Sources | Pull request diff and comments (untrusted: any contributor writes them) |
| Sinks | Review text; read-only git (diff, log, show) |
| Tools | `list_files`, `read_file`, `git_read`, all through `ToolGateway` |
| Identity | `ANTHROPIC_API_KEY`, never passed to tools; intended `GITHUB_TOKEN` limited to reading code and writing PR comments |
| Autonomy | Acts alone, no human approval |

## Run it on a Mac

1. Python 3.11 or later:
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
2. Pick a model:
   - **Local (free):** install Ollama ([ollama.com/download](https://ollama.com/download) or `brew install ollama`), then `ollama pull qwen2.5-coder:1.5b` (about 1 GB). Keep `LLM_BACKEND=ollama` in `.env`.
   - **Claude:** create a key in the Anthropic Console and set a low monthly spend limit there. Put it only in your local `.env` as `ANTHROPIC_API_KEY=...` and set `LLM_BACKEND=anthropic`. Never paste the key in chat or commit it.
3. Load the settings and run a review:
   ```
   set -a; source .env; set +a
   python -m agent.run_review prs/pr-000-clean.diff
   ```

## Tests

The tests use a scripted fake model, so they need no model and no key:

```
LLM_BACKEND=fake python -m pytest -q
```

The attack tests in `tests/test_attacks.py` assert the safe behaviour. In phase 3 they were expected failures, because the weaknesses were planted. Phase 6 fixed them, so they now pass and prove each fix holds. To see the attacks succeed, check out the last commit before the phase 6 fix PR and run `python -m pytest -q --runxfail tests/test_attacks.py`.

