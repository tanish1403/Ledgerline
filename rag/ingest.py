"""PDF parsing, chunking, deduplication, and document versioning pipeline."""

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.rag_models import Chunk, Document
from rag.embedder import embedder


def compute_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def ingest_pdf(db: Session, filename: str, file_bytes: bytes, role_access: str = "analyst", chunk_size: int = 500, overlap: int = 50) -> Document:
    """Ingest PDF by page, check content hash for deduplication/versioning."""
    content_hash = compute_hash(file_bytes)

    # Check if latest version with same content hash already exists
    existing = db.scalars(
        select(Document).filter(Document.filename == filename).order_by(Document.version.desc())
    ).first()

    if existing and existing.content_hash == content_hash:
        return existing  # Unchanged, skip re-ingestion

    new_version = (existing.version + 1) if existing else 1
    now = datetime.now(UTC).isoformat()

    doc = Document(
        filename=filename,
        version=new_version,
        content_hash=content_hash,
        created_at=now,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Parse PDF using pypdf if available, else fallback to text extraction simulation
    pages_text = []
    try:
        import io

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append((page_num, txt))
    except Exception:
        # Fallback if pypdf fails or mock
        pages_text = [(1, file_bytes.decode("utf-8", errors="ignore"))]

    all_texts = []
    chunk_meta = []
    for page_num, page_txt in pages_text:
        for ch in chunk_text(page_txt, chunk_size=chunk_size, overlap=overlap):
            if ch.strip():
                all_texts.append(ch)
                chunk_meta.append((page_num, ch))

    if all_texts:
        vectors = embedder.embed(all_texts)
        for (page_num, ch), vec in zip(chunk_meta, vectors):
            chunk = Chunk(
                document_id=doc.id,
                page=page_num,
                text=ch,
                embedding=vec,
                role_access=role_access,
            )
            db.add(chunk)
        db.commit()

    return doc
