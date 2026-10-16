"""Alembic migration: create jobs table."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_create_jobs"
down_revision = "0001_create_users_and_datasets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "succeeded", "failed", name="job_status_enum"),
            nullable=False,
        ),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_jobs_idempotency_key"), "jobs", ["idempotency_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_idempotency_key"), table_name="jobs")
    op.drop_table("jobs")
    op.execute("DROP TYPE job_status_enum;")
