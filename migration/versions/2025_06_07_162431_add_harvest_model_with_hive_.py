"""Add Harvest model with hive relationship and JSONB quality metrics

Revision ID: fd9c17d1e8b2
Revises: 1ef40438c63d
Create Date: 2025-06-07 16:24:31.158272+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fd9c17d1e8b2"
down_revision: str | None = "1ef40438c63d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "harvests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hive_id", sa.Integer(), nullable=False),
        sa.Column("yield_kg", sa.Double(), nullable=False),
        sa.Column(
            "quality_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("harvested_at", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["hive_id"], ["hives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_harvests_hive_id"), "harvests", ["hive_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_harvests_hive_id"), table_name="harvests")
    op.drop_table("harvests")
