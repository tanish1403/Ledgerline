"""LLM client and FakeLLM test double.

Wraps the OpenAI-compatible client (`openai.OpenAI`) and provides a FakeLLM
test double that replays scripted responses without network calls.
"""

from typing import Any

import openai

from api.config import settings


class LLMClient:
    """Thin wrapper around openai.OpenAI client pointing at LLM_BASE_URL."""

    def __init__(self) -> None:
        self.client = openai.OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
        self.model = settings.llm_model

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Execute a chat completion request."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(**kwargs)


class FakeLLM:
    """Test double that replays scripted responses for testing the agent loop."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.call_history: list[dict[str, Any]] = []

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        self.call_history.append({"messages": messages, "tools": tools})
        if not self.responses:
            raise RuntimeError("FakeLLM ran out of scripted responses.")
        return self.responses.pop(0)
