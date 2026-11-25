"""The gateway backend speaks OpenAI tool calls and sends only this app's own key (CS54 phase 7)."""
import io
import json

from agent import models
from agent.tools import SCHEMAS


def test_gateway_backend_parses_a_tool_call_and_uses_the_app_key(monkeypatch):
    sent = {}

    def fake_urlopen(req, timeout):
        sent.update(body=json.loads(req.data), auth=req.get_header("Authorization"))
        call = {"function": {"name": "read_file", "arguments": json.dumps({"path": "prs/pr-000-clean.diff"})}}
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": None, "tool_calls": [call]}}]}).encode())

    monkeypatch.setenv("LLM_BACKEND", "gateway")
    monkeypatch.setenv("GATEWAY_KEY", "sk-lab-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)
    step = models.next_step("system", [{"role": "user", "content": "Review prs/pr-000-clean.diff"}], SCHEMAS)
    assert step == ("tool", "read_file", {"path": "prs/pr-000-clean.diff"})
    assert sent["auth"] == "Bearer sk-lab-test"
    assert [t["function"]["name"] for t in sent["body"]["tools"]] == ["list_files", "read_file", "git_read"]
