"""Tool registry and RBAC enforcement.

A Tool bundles a name, description, Pydantic input model, allowed roles,
and callable. The registry builds JSON schemas for the model and validates
user role authorization before execution.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from api.db.models import Role


class Tool:
    """Represents an agent-callable tool with RBAC and schema generation."""

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: type[BaseModel],
        allowed_roles: list[Role],
        func: Callable[..., Any],
    ) -> None:
        self.name = name
        self.description = description
        self.args_schema = args_schema
        self.allowed_roles = allowed_roles
        self.func = func

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI function calling tool schema format."""
        schema = self.args_schema.model_json_schema()
        # Clean up schema for OpenAI function format if needed
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


class ToolRegistry:
    """Registry managing available tools and permission checks."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas_for_role(self, role: Role) -> list[dict[str, Any]]:
        """Return OpenAI tool schemas allowed for the given role."""
        return [
            tool.to_openai_schema()
            for tool in self._tools.values()
            if role in tool.allowed_roles or Role.admin in tool.allowed_roles
        ]

    def execute(self, name: str, args: dict[str, Any], role: Role) -> Any:
        """Execute a tool after verifying role permissions."""
        tool = self.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found."}

        if role not in tool.allowed_roles and role != Role.admin:
            return {"error": f"Role '{role}' is not allowed to use tool '{name}'."}

        try:
            # Validate args using Pydantic model
            parsed_args = tool.args_schema(**args)
            return tool.func(**parsed_args.model_dump())
        except Exception as exc:
            return {"error": f"Tool execution failed: {str(exc)}"}


# Global tool registry instance
registry = ToolRegistry()
