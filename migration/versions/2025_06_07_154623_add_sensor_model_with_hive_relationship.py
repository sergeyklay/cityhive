"""Add Sensor model with hive relationship

Revision ID: 66aabb72009f
Revises: ef3278621dbb
Create Date: 2025-06-07 15:46:23.361159+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "66aabb72009f"
down_revision: str | None = "ef3278621dbb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hive_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column(
            "mounted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hive_id"], ["hives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensors_hive_id"), "sensors", ["hive_id"], unique=False)
    op.create_index(
        op.f("ix_sensors_mounted_at"), "sensors", ["mounted_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_sensors_mounted_at"), table_name="sensors")
    op.drop_index(op.f("ix_sensors_hive_id"), table_name="sensors")
    op.drop_table("sensors")
