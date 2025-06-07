"""Add Inspection model with hive relationship

Revision ID: 1ef40438c63d
Revises: ce248cc62585
Create Date: 2025-06-07 16:18:31.581204+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1ef40438c63d"
down_revision: str | None = "ce248cc62585"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "inspections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hive_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hive_id"], ["hives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspections_created_at"), "inspections", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_inspections_hive_id"), "inspections", ["hive_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_inspections_hive_id"), table_name="inspections")
    op.drop_index(op.f("ix_inspections_created_at"), table_name="inspections")
    op.drop_table("inspections")
