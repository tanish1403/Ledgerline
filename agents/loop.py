import json
from typing import Any

from pydantic import BaseModel

from api.db.models import Role
from tools.registry import registry
from validators.recompute import AgentAnswer, ValidationReport, validate_claims


class AgentRunResult(BaseModel):
    answer: AgentAnswer
    transcript: list[dict[str, Any]]
    validated: bool
    validation_report: ValidationReport | None = None

class AgentLoop:
    def __init__(self, llm: Any, role: Role, max_steps: int = 5, max_json_retries: int = 3) -> None:
        self.llm = llm
        self.role = role
        self.max_steps = max_steps
        self.max_json_retries = max_json_retries

    def run(self, prompt: str) -> AgentRunResult:
        tools_schemas = registry.schemas_for_role(self.role)
        messages = [
            {"role": "system", "content": "You are a reliable agent. Output JSON AgentAnswer."},
            {"role": "user", "content": prompt},
        ]
        transcript = []
        tools_used_set = set()

        for _ in range(self.max_steps):
            response = self.llm.chat_completion(messages=messages, tools=tools_schemas)
            choice = response.choices[0]
            message = choice.message
            msg_dict = {"role": "assistant", "content": message.content}
            if message.tool_calls:
                msg_dict["tool_calls"] = [
                    {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in message.tool_calls
                ]
                messages.append(message.model_dump())
                transcript.append(msg_dict)
                for tc in message.tool_calls:
                    func_name = tc.function.name
                    try:
                        func_args = json.loads(tc.function.arguments)
                    except:
                        func_args = {}
                    tools_used_set.add(func_name)
                    tool_result = registry.execute(func_name, func_args, self.role)
                    tool_msg = {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(tool_result)}
                    messages.append(tool_msg)
                    transcript.append(tool_msg)
            else:
                messages.append(message.model_dump())
                transcript.append(msg_dict)
                content = message.content or ""
                answer = self._parse_and_validate(content, list(tools_used_set))
                if answer:
                    report = validate_claims(answer)
                    if report.passed:
                        return AgentRunResult(answer=answer, transcript=transcript, validated=True, validation_report=report)
                    else:
                        corr = {"role": "user", "content": f"Validation failed: {report.model_dump_json()}. Correct claims."}
                        messages.append(corr)
                        transcript.append(corr)
                        resp_retry = self.llm.chat_completion(messages=messages, tools=tools_schemas)
                        msg_retry = resp_retry.choices[0].message
                        messages.append(msg_retry.model_dump())
                        transcript.append({"role": "assistant", "content": msg_retry.content})
                        ans_retry = self._parse_and_validate(msg_retry.content or "", list(tools_used_set))
                        if ans_retry:
                            report_retry = validate_claims(ans_retry)
                            return AgentRunResult(answer=ans_retry, transcript=transcript, validated=report_retry.passed, validation_report=report_retry)
                        return AgentRunResult(answer=answer, transcript=transcript, validated=False, validation_report=report)
                else:
                    for _ in range(self.max_json_retries):
                        corr = {"role": "user", "content": "Invalid JSON. Output valid AgentAnswer JSON."}
                        messages.append(corr)
                        transcript.append(corr)
                        resp_retry = self.llm.chat_completion(messages=messages, tools=tools_schemas)
                        msg_retry = resp_retry.choices[0].message
                        messages.append(msg_retry.model_dump())
                        transcript.append({"role": "assistant", "content": msg_retry.content})
                        ans = self._parse_and_validate(msg_retry.content or "", list(tools_used_set))
                        if ans:
                            report = validate_claims(ans)
                            return AgentRunResult(answer=ans, transcript=transcript, validated=report.passed, validation_report=report)
                    raise ValueError("Failed to produce valid AgentAnswer JSON after retries.")
        raise ValueError("Agent reached max steps without returning a final answer.")

    def _parse_and_validate(self, content: str, tools_used: list[str]) -> AgentAnswer | None:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                if "tool_calls_used" not in data or not data["tool_calls_used"]:
                    data["tool_calls_used"] = tools_used
                return AgentAnswer(**data)
        except:
            pass
        return None
