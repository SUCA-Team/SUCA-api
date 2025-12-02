"""Base database model with common functionality."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseTable(SQLModel):
    """Base table with common fields."""

    created_at: datetime | None = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default_factory=datetime.now)
