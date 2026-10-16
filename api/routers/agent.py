"""Agent API router.

Provides POST /agent/runs (analyst+) running the agent loop and returning
the structured answer and transcript.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import tools  # noqa: F401
from agents.llm import LLMClient
from agents.loop import AgentLoop, AgentRunResult
from api.db.models import Role, User
from api.db.session import get_db
from api.deps import require_role

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRunIn(BaseModel):
    prompt: str = Field(..., min_length=1)


@router.post("/runs", response_model=AgentRunResult, status_code=status.HTTP_200_OK)
def run_agent(
    body: AgentRunIn,
    db: Session = Depends(get_db),  # noqa: B008
    user: User = Depends(require_role(Role.analyst, Role.admin)),  # noqa: B008
):
    """Run the agent loop with the calling user's role and return structured answer + transcript."""
    llm = LLMClient()
    agent = AgentLoop(llm=llm, role=user.role)
    result = agent.run(body.prompt)
    return result
