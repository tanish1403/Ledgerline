"""RAG API router for question answering with citations and confidence flags."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.dependencies import get_current_user
from api.db.models import User
from rag.qa import answer_question, RAGAnswer


router = APIRouter(prefix="/rag", tags=["rag"])


class RAGRequest(BaseModel):
    query: str = Field(..., description="Question to ask against reliability documentation.")


@router.post("/ask", response_model=RAGAnswer)
def ask_rag(
    req: RAGRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RAGAnswer:
    """Ask a question against RAG knowledge base respecting user role access."""
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    result = answer_question(db, req.query, role=role)
    return result
