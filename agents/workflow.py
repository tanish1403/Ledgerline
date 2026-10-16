"""LangGraph workflow definition with interruption before consequential actions and Postgres checkpointer."""

from typing import Annotated, Any, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from tools.inspection_tools import flag_units_for_inspection


class AgentWorkflowState(TypedDict):
    messages: list[dict[str, Any]]
    unit_ids: list[int]
    reason: str
    flag_id: int | None
    status: str


def analysis_node(state: AgentWorkflowState) -> dict[str, Any]:
    """Perform reliability analysis before flagging."""
    return {"status": "analyzed"}


def inspection_flag_node(state: AgentWorkflowState) -> dict[str, Any]:
    """Consequential action node (requires approval checkpoint before execution)."""
    res = flag_units_for_inspection(
        unit_ids=state["unit_ids"],
        reason=state["reason"],
    )
    return {"flag_id": res["flag_id"], "status": res["status"]}


def create_approval_workflow(checkpointer: Any = None) -> Any:
    """Build LangGraph workflow with interrupt before inspection flagging."""
    workflow = StateGraph(AgentWorkflowState)

    workflow.add_node("analysis", analysis_node)
    workflow.add_node("flag_inspection", inspection_flag_node)

    workflow.add_edge(START, "analysis")
    workflow.add_edge("analysis", "flag_inspection")
    workflow.add_edge("flag_inspection", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    # Compile graph with interrupt before consequential node
    app = workflow.compile(checkpointer=checkpointer, interrupt_before=["flag_inspection"])
    return app
