"""Functional tests with the fake model. Attack tests arrive in phase 3."""
from agent import tools
from agent.run_review import review


def test_clean_diff_gets_a_clean_review():
    text, calls = review("prs/pr-000-clean.diff", log=lambda *_: None)
    assert "No security problems" in text
    assert calls == [{"tool": "read_file", "args": {"path": "prs/pr-000-clean.diff"}}]


def test_tool_registry_matches_schemas():
    assert set(tools.TOOLS) == {s["name"] for s in tools.SCHEMAS}


def test_list_files_shows_workspace():
    assert "app/orders.py" in tools.list_files()
