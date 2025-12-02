"""FastAPI dependencies for dependency injection."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from ..db.db import get_engine
from ..services.search_service import SearchService


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a database Session and ensure it is closed."""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def get_search_service(session: Annotated[Session, Depends(get_session)]) -> SearchService:
    """FastAPI dependency: get SearchService instance."""
    return SearchService(session)


# Type aliases for commonly used dependencies
SessionDep = Annotated[Session, Depends(get_session)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
