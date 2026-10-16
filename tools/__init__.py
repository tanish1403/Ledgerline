"""Register default tools into the global registry."""

from api.db.models import Role
from tools.calculator import CalculatorArgs, calculator
from tools.file_reader import FileReaderArgs, read_file
from tools.registry import Tool, registry
from tools.sql import SqlQueryArgs, sql_query

registry.register(
    Tool(
        name="sql_query",
        description="Run a read-only SELECT query against allowed tables (users, datasets, jobs).",
        args_schema=SqlQueryArgs,
        allowed_roles=[Role.analyst, Role.admin],
        func=sql_query,
    )
)

registry.register(
    Tool(
        name="calculator",
        description="Evaluate arithmetic expressions safely.",
        args_schema=CalculatorArgs,
        allowed_roles=[Role.viewer, Role.analyst, Role.admin],
        func=calculator,
    )
)

registry.register(
    Tool(
        name="read_file",
        description="Read text files strictly within the sandbox directory.",
        args_schema=FileReaderArgs,
        allowed_roles=[Role.analyst, Role.admin],
        func=read_file,
    )
)
