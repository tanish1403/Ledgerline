"""Sandboxed SQL query tool.

Allows ONE read-only SELECT statement against an allow-list of tables,
with a statement timeout and row limit, executed in a read-only transaction.
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from api.db.session import SessionLocal

ALLOWED_TABLES = {"users", "datasets", "jobs"}


class SqlQueryArgs(BaseModel):
    query: str = Field(..., description="A single read-only SELECT SQL query.")


def sql_query(query: str) -> list[dict[str, Any]] | dict[str, str]:
    """Execute a sandboxed, read-only SELECT query against allowed tables."""
    cleaned = query.strip().rstrip(";")

    # Reject multiple statements (semicolons inside or trailing)
    if ";" in cleaned:
        return {"error": "Multiple SQL statements are not allowed."}

    # Reject comments (-- or /* */)
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        return {"error": "SQL comments are not allowed."}

    # Must start with SELECT
    if not cleaned.upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are permitted."}

    # Check for forbidden write/DDL keywords
    forbidden_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
    ]
    upper_query = cleaned.upper()
    for kw in forbidden_keywords:
        # Match whole word
        if re.search(r"\b" + kw + r"\b", upper_query):
            return {"error": f"Keyword '{kw}' is not allowed in queries."}

    # Extract table names referenced and ensure they are in allow-list
    # Simple regex looking for FROM or JOIN followed by table name
    table_pattern = r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    referenced_tables = re.findall(table_pattern, upper_query)
    for tbl in referenced_tables:
        if tbl.lower() not in ALLOWED_TABLES:
            return {"error": f"Table '{tbl}' is not allow-listed."}

    # Ensure query has LIMIT clause or enforce max rows
    if "LIMIT" not in upper_query:
        cleaned = f"{cleaned} LIMIT 100"

    db = SessionLocal()
    try:
        # Set read-only transaction and statement timeout
        db.execute(
            __import__("sqlalchemy").text(
                "SET LOCAL transaction_read_only = ON; SET LOCAL statement_timeout = '2s';"
            )
        )
        result = db.execute(__import__("sqlalchemy").text(cleaned))
        columns = result.keys()
        rows = [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
        return rows
    except Exception as exc:
        db.rollback()
        return {"error": f"SQL execution error: {str(exc)}"}
    finally:
        db.close()
