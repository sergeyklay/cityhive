import uuid
from datetime import datetime

import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy import orm as so
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func


class RecordNotFound(Exception):
    """Requested record in database was not found"""


class Base(so.DeclarativeBase):
    """Base class for all models."""

    @classmethod
    async def get_or_fail(cls, session: AsyncSession, entity_id: int):
        """Return the model with the specified identifier.

        Args:
            session: The database session to use.
            entity_id: The identifier of the model to return.

        Returns:
            The model with the specified identifier.

        Raises:
            RecordNotFound: If the model with the specified identifier does not exist.
        """
        result = await session.get(cls, entity_id)
        if not result:
            raise RecordNotFound(f"{cls.__name__} with id: {entity_id} does not exist")
        return result


class IdentityMixin:
    """Mixin class to add identity fields to a SQLAlchemy model."""

    id: so.Mapped[int] = so.mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    def __repr__(self):
        """Returns the object representation in string format."""
        return f"<{self.__class__.__name__} id={self.id!r}>"


class User(Base, IdentityMixin):
    """User model."""

    __tablename__ = "users"

    name: so.Mapped[str] = so.mapped_column(
        sa.String(100),
        nullable=False,
    )
    email: so.Mapped[str] = so.mapped_column(
        sa.String(254),
        unique=True,
        nullable=False,
        index=True,
    )
    api_key: so.Mapped[UUID] = so.mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
        unique=True,
        index=True,
    )
    registered_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )

    hives: so.Mapped[list["Hive"]] = so.relationship(back_populates="user")


class Hive(Base, IdentityMixin):
    """Hive model."""

    __tablename__ = "hives"

    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: so.Mapped[str] = so.mapped_column(
        sa.Text,
        nullable=False,
    )
    location: so.Mapped[Geography | None] = so.mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    frame_type: so.Mapped[str] = so.mapped_column(
        sa.Text,
        nullable=True,
    )
    installed_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )

    user: so.Mapped["User"] = so.relationship(back_populates="hives")
    sensors: so.Mapped[list["Sensor"]] = so.relationship(back_populates="hive")


class Sensor(Base, IdentityMixin):
    """Sensor model."""

    __tablename__ = "sensors"

    hive_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("hives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: so.Mapped[str] = so.mapped_column(
        sa.Text,
        nullable=False,
    )
    mounted_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )

    hive: so.Mapped["Hive"] = so.relationship(back_populates="sensors")
