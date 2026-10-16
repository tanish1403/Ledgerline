"""Tests for Milestone 3: framework-free agent loop, sandboxed tools, and security."""

import json
from pathlib import Path

import pytest

from agents.llm import FakeLLM
from agents.loop import AgentLoop
from api.db.models import Role
from tools.file_reader import read_file
from tools.registry import registry
from tools.sql import sql_query


class MockToolCall:
    def __init__(self, id: str, name: str, arguments: str) -> None:
        self.id = id
        self.function = MockFunction(name, arguments)
        self.model_dump = lambda: {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": id,
                    "function": {"name": name, "arguments": arguments},
                }
            ],
        }


class MockFunction:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class MockMessage:
    def __init__(self, content: str | None, tool_calls: list | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self) -> dict:
        return {"role": "assistant", "content": self.content}


class MockChoice:
    def __init__(self, message: MockMessage) -> None:
        self.message = message


class MockResponse:
    def __init__(self, message: MockMessage) -> None:
        self.choices = [MockChoice(message)]


def test_agent_happy_path():
    resp1 = MockResponse(
        MockMessage(
            None,
            [MockToolCall("call_1", "calculator", json.dumps({"expression": "100 + 200"}))],
        )
    )
    final_answer_json = json.dumps(
        {
            "summary": "Calculated total.",
            "claims": ["Sum is 300"],
            "tool_calls_used": ["calculator"],
        }
    )
    resp2 = MockResponse(MockMessage(final_answer_json))

    fake_llm = FakeLLM([resp1, resp2])
    agent = AgentLoop(llm=fake_llm, role=Role.analyst)

    result = agent.run("Calculate sum.")
    assert result.answer.summary == "Calculated total."
    assert len(result.transcript) > 0


def test_forbidden_tool_rejected():
    res = registry.execute("sql_query", {"query": "SELECT * FROM users"}, Role.viewer)
    assert "error" in res


def test_sql_security_validations():
    assert "error" in sql_query("SELECT * FROM users; DROP TABLE users;")
    assert "error" in sql_query("SELECT * FROM users -- comment")
    assert "error" in sql_query("UPDATE users SET email = 'hacked'")
    assert "error" in sql_query("SELECT * FROM secrets")


def test_file_reader_sandbox():
    sandbox = Path(__file__).resolve().parent.parent / "sandbox"
    sandbox.mkdir(exist_ok=True)
    test_file = sandbox / "notes.txt"
    test_file.write_text("hello sandbox")

    assert read_file("notes.txt")["content"] == "hello sandbox"
    assert "error" in read_file("../pyproject.toml")


def test_agent_invalid_json_retry_failure():
    resp_bad = MockResponse(MockMessage("Not JSON"))
    fake_llm = FakeLLM([resp_bad, resp_bad, resp_bad])
    agent = AgentLoop(llm=fake_llm, role=Role.analyst, max_json_retries=1)

    with pytest.raises(ValueError, match="Failed to produce valid AgentAnswer JSON"):
        agent.run("Give me JSON")


def test_agent_max_steps_stop():
    resp_tool = MockResponse(
        MockMessage(
            None,
            [MockToolCall("call_inf", "calculator", json.dumps({"expression": "1 + 1"}))],
        )
    )
    fake_llm = FakeLLM([resp_tool, resp_tool, resp_tool])
    agent = AgentLoop(llm=fake_llm, role=Role.analyst, max_steps=2)

    with pytest.raises(ValueError, match="Agent reached max steps"):
        agent.run("Loop forever")
