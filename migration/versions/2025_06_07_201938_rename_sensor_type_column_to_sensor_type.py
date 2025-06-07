"""Rename sensor type column to sensor_type

Revision ID: f041a85e0cd4
Revises: fd9c17d1e8b2
Create Date: 2025-06-07 20:19:38.262336+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f041a85e0cd4"
down_revision: str | None = "fd9c17d1e8b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "sensors",
        "type",
        new_column_name="sensor_type",
        existing_type=sa.Text(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "sensors",
        "sensor_type",
        new_column_name="type",
        existing_type=sa.Text(),
        nullable=False,
    )
