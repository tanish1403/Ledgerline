"""Alembic migration for documents and chunks tables with pgvector extension."""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "007_rag_tables"
down_revision = "006_inspection_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(50), nullable=False),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("tsv", sa.Text(), nullable=True),
        sa.Column("role_access", sa.String(50), nullable=False, server_default="analyst"),
    )

    # Indexes
    op.execute("CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX idx_chunks_tsv ON chunks USING gin (to_tsvector('english', text));")


def downgrade() -> None:
    op.drop_table("chunks")
    op.drop_table("documents")
