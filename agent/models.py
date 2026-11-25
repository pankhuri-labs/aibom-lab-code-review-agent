"""Model backends. Each returns ("tool", name, args) or ("final", text, None)."""
import json
import os
import re
import urllib.request


def next_step(system: str, history: list[dict], schemas: list[dict]):
    backend = os.environ.get("LLM_BACKEND", "ollama")
    return {"anthropic": _claude, "ollama": _ollama, "gateway": _gateway, "fake": _fake}[backend](system, history, schemas)


def _claude(system, history, schemas):
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    messages = []
    for h in history:
        if h["role"] == "tool":
            messages.append({"role": "user", "content": f"Tool {h['name']} returned:\n{h['content']}"})
        else:
            messages.append({"role": h["role"], "content": h["content"]})
    resp = client.messages.create(model=os.environ.get("REVIEW_MODEL_CLAUDE", "claude-haiku-5-5"),
                                  max_tokens=2000, system=system, tools=schemas, messages=messages)
    for block in resp.content:
        if block.type == "tool_use":
            return ("tool", block.name, block.input)
    return ("final", "".join(b.text for b in resp.content if b.type == "text"), None)


def _ollama(system, history, schemas):
    tools = [{"type": "function", "function": {"name": s["name"], "description": s["description"],
                                               "parameters": s["input_schema"]}} for s in schemas]
    messages = [{"role": "system", "content": system}]
    for h in history:
        role = "tool" if h["role"] == "tool" else h["role"]
        messages.append({"role": role, "content": h["content"]})
    payload = {"model": os.environ.get("REVIEW_MODEL_OLLAMA", "qwen2.5-coder:1.5b"),
               "messages": messages, "tools": tools, "stream": False}
    req = urllib.request.Request(f"{os.environ.get('OLLAMA_URL', 'http://localhost:11434')}/api/chat",
                                 data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        msg = json.loads(resp.read())["message"]
    calls = msg.get("tool_calls") or []
    if calls:
        fn = calls[0]["function"]
        return ("tool", fn["name"], fn.get("arguments") or {})
    return ("final", msg.get("content", ""), None)


def _gateway(system, history, schemas):
    """Phase 7: OpenAI-compatible call through the CS54 gateway. The gateway holds the provider keys,
    so this process needs only its own GATEWAY_KEY; GATEWAY_MODEL picks Claude or Qwen from the AI-BOM."""
    tools = [{"type": "function", "function": {"name": s["name"], "description": s["description"],
                                               "parameters": s["input_schema"]}} for s in schemas]
    messages = [{"role": "system", "content": system}]
    for h in history:
        if h["role"] == "tool":
            messages.append({"role": "user", "content": f"Tool {h['name']} returned:\n{h['content']}"})
        else:
            messages.append({"role": h["role"], "content": h["content"]})
    payload = {"model": os.environ.get("GATEWAY_MODEL", "qwen2.5-coder:1.5b"), "messages": messages,
               "tools": tools, "max_tokens": 2000}
    req = urllib.request.Request(f"{os.environ.get('GATEWAY_URL', 'http://localhost:4000')}/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {os.environ['GATEWAY_KEY']}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        msg = json.loads(resp.read())["choices"][0]["message"]
    calls = msg.get("tool_calls") or []
    if calls:
        fn = calls[0]["function"]
        args = fn.get("arguments") or "{}"
        return ("tool", fn["name"], json.loads(args) if isinstance(args, str) else args)
    return ("final", msg.get("content") or "", None)


def _fake(system, history, schemas):
    """Scripted model with no defences: reads the diff, obeys any RUN: line it finds, then reports."""
    tool_turns = [h for h in history if h["role"] == "tool"]
    if not tool_turns:
        diff = re.search(r"(prs/\S+\.diff)", history[0]["content"]).group(1)
        return ("tool", "read_file", {"path": diff})
    last = tool_turns[-1]
    if last["name"] == "read_file":
        run = re.search(r"RUN: (.+)", last["content"])
        if run:
            return ("tool", "run_shell", {"command": run.group(1).strip()})
        if "f\"SELECT" in last["content"] or "f'SELECT" in last["content"]:
            return ("final", "app/orders.py: SQL built with an f-string (SQL injection). Use a parameterised query.", None)
        return ("final", "No security problems found in the diff.", None)
    return ("final", "Setup step done. Review: app/orders.py builds SQL with an f-string; use a parameterised query.", None)
