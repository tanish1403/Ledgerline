"""Sandboxed calculator tool using AST parsing.

Safely evaluates arithmetic expressions with an allow-list of node types.
Never uses eval().
"""

import ast
from typing import Any

from pydantic import BaseModel, Field

ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.UAdd,
}


class CalculatorArgs(BaseModel):
    expression: str = Field(
        ...,
        description=("Arithmetic expression to evaluate (e.g. '10 + 20 * 3')."),
    )


def _eval_node(node: ast.AST) -> float | int:
    if type(node) not in ALLOWED_NODES:
        raise ValueError(f"Disallowed AST node type: {type(node).__name__}")

    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, int | float):
            return node.value
        raise ValueError(f"Disallowed constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero.")
            return left / right
        elif isinstance(node.op, ast.Pow):
            return left**right
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand

    raise ValueError("Invalid expression structure.")


def calculator(
    expression: str,
) -> dict[str, Any] | dict[str, str]:
    """Evaluate an arithmetic expression safely using AST parsing."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree)
        return {"result": result}
    except Exception as exc:
        return {"error": f"Calculation error: {str(exc)}"}
