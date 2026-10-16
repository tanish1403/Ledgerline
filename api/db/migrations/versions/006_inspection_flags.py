"""Alembic migration for inspection_flags table."""

from alembic import op
import sqlalchemy as sa


revision = "006_inspection_flags"
down_revision = "005_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inspection_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit_ids", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, index=True),
        sa.Column("requested_by", sa.String(100), nullable=False),
        sa.Column("decided_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("decided_at", sa.String(50), nullable=True),
        sa.Column("applied_at", sa.String(50), nullable=True),
        sa.Column("rolled_back_at", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("inspection_flags")
