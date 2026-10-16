# Prompt 03: Tool-calling agent from scratch

Tag the start: `git tag milestone-3-start`.

```
Milestone 3: an agent loop with no agent framework. Milestone 1 must be done.

Goal: understand exactly what agent frameworks hide. Use the `openai` Python client pointed at
LLM_BASE_URL (OmniRoute or Ollama), so any OpenAI-compatible model works.

Build:
1. tools/registry.py: a Tool is (name, description, Pydantic input model, allowed_roles, callable).
   The registry builds the JSON schema sent to the model and refuses to call a tool the user's role
   does not allow.
2. Three tools:
   - sql_query: ONE read-only SELECT, against an allow-list of tables, with a statement timeout and a row
     limit. Reject everything else (multiple statements, writes, comments tricks). Run it on a read-only
     transaction.
   - calculator: arithmetic via the `ast` module with an allow-list of node types. Never `eval`.
   - read_file: reads text files only inside a sandbox directory. Reject `..`, absolute paths and symlinks
     that escape.
3. agents/loop.py: the loop sends messages, runs requested tools, feeds results back, stops at a max step
   count. The final answer must validate as a Pydantic `AgentAnswer` (summary, claims list, tool_calls_used).
   On invalid JSON, retry up to N times with the validation error in the message, then fail cleanly.
4. agents/llm.py: a thin client plus a `FakeLLM` test double that replays scripted responses.
5. POST /agent/runs (analyst+) runs the agent and returns the answer and a step transcript.
   Keep the transcript in memory for now; the audit log arrives in milestone 5.

Tests (all with FakeLLM, no network):
- happy path with two tool calls
- model asks for a forbidden tool (rejected and reported back to the model)
- SQL injection attempts and multi-statement SQL are rejected
- path traversal and symlink escape are rejected
- invalid JSON from the model is retried, then fails after N attempts
- max steps stops an infinite loop

Acceptance criteria: `make test`, `make lint`, CI green, docs/PROGRESS.md updated, and a short
docs/agent_loop.md explaining the loop in under one page.

Out of scope: LangGraph, approvals, stats. Ask before adding dependencies. Show me the plan first.
Commit message: feat: framework-free tool-calling agent with sandboxed tools
```
