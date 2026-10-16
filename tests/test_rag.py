"""Unit tests for RAG ingestion, hybrid retrieval, citation verification, and confidence scoring."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.db.models import Base, Role, User
from rag.ingest import ingest_pdf
from rag.qa import answer_question, verify_citation, Citation, RAGAnswer


@pytest.fixture
def rag_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


def test_pdf_ingestion_and_versioning(rag_db):
    pdf_bytes = b"Turbine bearing failure usually occurs due to excessive vibration and thermal overload on page one."
    doc1 = ingest_pdf(rag_db, filename="turbine_manual.pdf", file_bytes=pdf_bytes, role_access="analyst")
    assert doc1.version == 1

    # Ingest unchanged -> returns same doc
    doc2 = ingest_pdf(rag_db, filename="turbine_manual.pdf", file_bytes=pdf_bytes, role_access="analyst")
    assert doc2.id == doc1.id
    assert doc2.version == 1

    # Ingest changed content -> new version
    changed_bytes = b"Turbine bearing failure usually occurs due to excessive vibration and thermal overload on page one. Updated specs."
    doc3 = ingest_pdf(rag_db, filename="turbine_manual.pdf", file_bytes=changed_bytes, role_access="analyst")
    assert doc3.version == 2
    assert doc3.id != doc1.id


def test_citation_verification():
    chunks = [
        {"filename": "manual.pdf", "page": 1, "text": "Bearing failure occurs at high temperatures."},
    ]
    valid_cit = Citation(document="manual.pdf", page=1, quote="Bearing failure")
    assert verify_citation(valid_cit, chunks) is True

    invalid_cit = Citation(document="manual.pdf", page=1, quote="Nonexistent quote")
    assert verify_citation(invalid_cit, chunks) is False


def test_rag_qa_unanswerable(rag_db):
    result = answer_question(rag_db, "What is the capital of France?", role="analyst")
    assert result.answer == "not found"
    assert result.is_confident is False
