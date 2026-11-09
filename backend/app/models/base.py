"""Base declarative models and mixins for ReproCheck SQLAlchemy ORM.

Provides the common Base class with AsyncAttrs support for modern
SQLAlchemy 2.0 asynchronous execution and timestamp mixins for audit tracking.
"""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Declarative Base class for all application database models.

    Inherits from AsyncAttrs to allow lazy loading of relationships
    within async execution contexts via `await model.awaitable_attrs.relationship`.
    """
    pass


class TimestampMixin:
    """Reusable mixin providing created_at and updated_at timestamp columns.

    Uses timezone-aware timestamps with server-side defaults.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp when the record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="UTC timestamp when the record was last modified.",
    )
