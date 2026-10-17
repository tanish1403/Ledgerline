"""Alembic migration for audit_events table and append-only trigger."""

import sqlalchemy as sa
from alembic import op

revision = "005_audit_events"
down_revision = "004_reliability"  # or previous milestone revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.String(50), nullable=False),
        sa.Column("actor_user_id", sa.String(100), nullable=True),
        sa.Column("actor_role", sa.String(50), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("resource", sa.String(200), nullable=True),
        sa.Column("inputs", sa.Text(), nullable=True),
        sa.Column("outputs", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(100), nullable=True, index=True),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
    )

    # Append-only trigger for PostgreSQL
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit log is append-only. UPDATE and DELETE are strictly prohibited.';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_append_only_trigger
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_append_only_trigger ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
    op.drop_table("audit_events")
