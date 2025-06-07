"""Add SensorReading model with sensor relationship

Revision ID: ce248cc62585
Revises: 66aabb72009f
Create Date: 2025-06-07 16:08:30.706132+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce248cc62585"
down_revision: str | None = "66aabb72009f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Double(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sensor_readings_recorded_at"),
        "sensor_readings",
        ["recorded_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sensor_readings_sensor_id"),
        "sensor_readings",
        ["sensor_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_sensor_readings_sensor_id"), table_name="sensor_readings")
    op.drop_index(op.f("ix_sensor_readings_recorded_at"), table_name="sensor_readings")
    op.drop_table("sensor_readings")
