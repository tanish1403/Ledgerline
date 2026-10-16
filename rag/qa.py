"""RAG question answering, citation verification, and confidence scoring."""

from typing import List, Optional
from pydantic import BaseModel, Field

from rag.retrieval import hybrid_retrieve


class Citation(BaseModel):
    document: str = Field(..., description="Filename of the source document.")
    page: int = Field(..., description="Page number of the citation.")
    quote: str = Field(..., description="Exact verbatim quote from the text chunk.")


class RAGAnswer(BaseModel):
    answer: str = Field(..., description="Answering text or 'not found'.")
    citations: List[Citation] = Field(default_factory=list)
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0.")
    is_confident: bool = Field(..., description="True if confidence is above calibration threshold.")


def verify_citation(citation: Citation, retrieved_chunks: List[dict]) -> bool:
    """Reject any citation whose quote is not found verbatim in the retrieved text."""
    for chunk in retrieved_chunks:
        if chunk["filename"] == citation.document and chunk["page"] == citation.page:
            if citation.quote.strip() in chunk["text"]:
                return True
    return False


def answer_question(db: any, query: str, role: str = "analyst", confidence_threshold: float = 0.4) -> RAGAnswer:
    """Retrieve chunks, generate answer with verified citations, and evaluate confidence."""
    chunks = hybrid_retrieve(db, query, role=role, top_k=5)

    if not chunks:
        return RAGAnswer(
            answer="not found",
            citations=[],
            confidence=0.0,
            is_confident=False,
        )

    # Compute confidence based on top retrieval score and coverage
    top_score = chunks[0].get("rrf_score", 0.5)
    # Normalize score to 0-1 range roughly
    confidence = min(max(top_score * 50.0, 0.1), 1.0)

    if confidence < confidence_threshold:
        return RAGAnswer(
            answer="not found",
            citations=[],
            confidence=confidence,
            is_confident=False,
        )

    # Construct answer from top chunks with citations
    top_chunk = chunks[0]
    sentence = top_chunk["text"][:200].strip()
    quote = sentence[: min(50, len(sentence))]

    citation = Citation(
        document=top_chunk["filename"],
        page=top_chunk["page"],
        quote=quote,
    )

    if not verify_citation(citation, chunks):
        return RAGAnswer(
            answer="not found",
            citations=[],
            confidence=confidence,
            is_confident=False,
        )

    return RAGAnswer(
        answer=f"Based on documentation, {sentence}",
        citations=[citation],
        confidence=confidence,
        is_confident=True,
    )
