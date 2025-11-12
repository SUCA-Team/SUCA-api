from src.suca.db.db import engine
from sqlmodel import Session


def get_session() -> Session:
    """FastAPI dependency: yield a Session and ensure it is closed."""
    with Session(engine) as session:
        yield session
        
def get_user_id():
    pass