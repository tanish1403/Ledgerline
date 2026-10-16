# Prompt 07: RAG module with citations

Tag the start: `git tag milestone-7-start`. Put 20+ public PDFs in `data/docs/` first.

```
Milestone 7: retrieval-augmented answers with citations and a confidence flag. Milestone 1 must be done.

Goal: every answer cites page-level sources, and weak answers are flagged instead of presented as fact.

Build:
1. documents and chunks tables with pgvector: chunks(id, document_id, page, text, embedding, tsv,
   role_access). HNSW index on the embedding, GIN index on the tsvector. Migration included.
   The embedding dimension must match the model you choose; record the model name in the table.
2. Embeddings through a small `rag/embedder.py` interface with two backends: sentence-transformers
   (bge-small) and Ollama embeddings. Pick one as default and tell me why. Ask before adding dependencies.
3. Ingestion script: parse PDFs by page, chunk with a configurable size and overlap, skip files whose
   content hash is unchanged, version a document when its content changes.
4. Hybrid retrieval: vector search plus Postgres full-text search, merged with reciprocal rank fusion.
5. Answering: the model sees only retrieved chunks and returns a Pydantic answer with citations
   (document, page, quote). Reject any citation whose quote is not found in the retrieved text.
6. Confidence flag: based on retrieval score and citation coverage. The threshold is calibrated on a set of
   known-answerable questions only (for example the 5th percentile of their scores), never on bad data.
7. Role filter: a user retrieves only chunks their role may see.
8. POST /rag/ask with a "not found" answer when evidence is missing.

Tests (small fixture PDFs, FakeLLM, deterministic fake embeddings):
- citations point at real chunks; a fabricated quote is rejected
- unanswerable question returns "not found"
- changed document is re-ingested as a new version; unchanged one is skipped
- role filter hides restricted chunks; confidence flag triggers below the threshold

Acceptance criteria: `make test`, `make lint`, CI green, docs/PROGRESS.md updated, and a chunk-size
comparison table (chunk size vs retrieval recall) added to docs/rag.md using your golden questions.

Commit message: feat: hybrid RAG with verified citations and calibrated confidence
```
