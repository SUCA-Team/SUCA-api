"""Base database model with common functionality."""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class BaseTable(SQLModel):
    """Base table with common fields."""
    
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
