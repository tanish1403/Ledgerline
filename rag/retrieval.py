"""Hybrid retrieval combining vector similarity and full-text search with Reciprocal Rank Fusion (RRF)."""

from typing import Any

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from rag.embedder import embedder


def reciprocal_rank_fusion(vector_results: list[dict[str, Any]], fts_results: list[dict[str, Any]], k: int = 60) -> list[dict[str, Any]]:
    """Merge vector and FTS results using Reciprocal Rank Fusion (RRF)."""
    scores: dict[int, float] = {}
    chunk_map: dict[int, dict[str, Any]] = {}

    for rank, item in enumerate(vector_results, start=1):
        cid = item["id"]
        chunk_map[cid] = item
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    for rank, item in enumerate(fts_results, start=1):
        cid = item["id"]
        chunk_map[cid] = item
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    sorted_chunk_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    merged = []
    for cid in sorted_chunk_ids:
        item = chunk_map[cid]
        item["rrf_score"] = scores[cid]
        merged.append(item)
    return merged


def hybrid_retrieve(db: Session, query: str, role: str = "analyst", top_k: int = 5) -> list[dict[str, Any]]:
    """Retrieve chunks using vector search and FTS, filtered by role access."""
    q_vec = embedder.embed([query])[0]

    # Role accessibility filter
    allowed_roles = ["analyst", "admin"] if role == "admin" else ["analyst"]

    # Vector search query (pgvector cosine similarity)
    vec_sql = sql_text("""
        SELECT c.id, c.document_id, c.page, c.text, c.role_access, d.filename,
               1 - (c.embedding <=> (:q_vec)::vector) AS sim
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.role_access = ANY(:roles)
        ORDER BY c.embedding <=> (:q_vec)::vector
        LIMIT :limit
    """)
    vec_rows = db.execute(vec_sql, {"q_vec": str(q_vec), "roles": allowed_roles, "limit": top_k * 2}).fetchall()
    vector_results = [
        {
            "id": r.id,
            "document_id": r.document_id,
            "page": r.page,
            "text": r.text,
            "filename": r.filename,
            "similarity": float(r.sim),
        }
        for r in vec_rows
    ]

    # Full-text search query
    fts_sql = sql_text("""
        SELECT c.id, c.document_id, c.page, c.text, c.role_access, d.filename,
               ts_rank_cd(to_tsvector('english', c.text), plainto_query('english', :query)) AS rank
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.role_access = ANY(:roles) AND to_tsvector('english', c.text) @@ plainto_query('english', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)
    fts_rows = db.execute(fts_sql, {"query": query, "roles": allowed_roles, "limit": top_k * 2}).fetchall()
    fts_results = [
        {
            "id": r.id,
            "document_id": r.document_id,
            "page": r.page,
            "text": r.text,
            "filename": r.filename,
            "rank": float(r.rank),
        }
        for r in fts_rows
    ]

    merged = reciprocal_rank_fusion(vector_results, fts_results)
    return merged[:top_k]
