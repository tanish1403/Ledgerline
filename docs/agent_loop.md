# Framework-Free Agent Loop

The Reliability Agent Platform implements a **framework-free agent loop** (`agents/loop.py`) rather than relying on black-box agent orchestration frameworks (like LangGraph or LangChain). This ensures every line of reasoning, tool execution, and state transition is transparent, fully testable, and explainable.

## Architecture

1. **LLM Client & Test Double (`agents/llm.py`)**:
   - Wraps the standard `openai.OpenAI` client pointing at any OpenAI-compatible endpoint (`LLM_BASE_URL` - OmniRoute or Ollama).
   - Provides `FakeLLM`, a test double that replays scripted responses without making network calls.

2. **Tool Registry & RBAC (`tools/registry.py`)**:
   - A `Tool` binds a name, description, Pydantic input schema, allowed roles (`list[Role]`), and a Python callable.
   - The registry generates OpenAI function-calling JSON schemas and enforces strict role authorization before invoking any tool.

3. **Sandboxed Tools (`tools/`)**:
   - **`sql_query`**: Restricts queries to a single read-only `SELECT` statement against an allow-list of tables (`users`, `datasets`, `jobs`), executed in a read-only transaction with a 2-second timeout and 100-row limit.
   - **`calculator`**: Safely evaluates arithmetic expressions via Python's `ast` module with an allow-list of node types (never uses `eval`).
   - **`read_file`**: Reads text files strictly inside the `./sandbox` directory, rejecting path traversal (`..`), absolute paths, and escaping symlinks.

4. **Reasoning-and-Acting Loop (`agents/loop.py`)**:
   - Manages message history (system, user, assistant, tool).
   - Iterates up to `max_steps` (default 5).
   - Feeds tool outputs back into conversation history.
   - Parses and validates the final response against a Pydantic `AgentAnswer` model (`summary`, `claims`, `tool_calls_used`).
   - Retries up to $N$ times with a correction prompt if the model outputs invalid JSON.
