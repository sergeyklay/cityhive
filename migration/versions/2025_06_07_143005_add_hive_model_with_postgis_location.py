"""Add Hive model with PostGIS location

Revision ID: ef3278621dbb
Revises: ecc1762414e2
Create Date: 2025-06-07 14:30:05.734653+00:00

"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef3278621dbb"
down_revision: str | None = "ecc1762414e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "hives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geography(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
        sa.Column("frame_type", sa.Text(), nullable=True),
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_hives_installed_at"), "hives", ["installed_at"], unique=False
    )
    op.create_index(op.f("ix_hives_user_id"), "hives", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_hives_user_id"), table_name="hives")
    op.drop_index(op.f("ix_hives_installed_at"), table_name="hives")
    op.drop_table("hives")
