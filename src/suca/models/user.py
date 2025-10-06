from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    email: str
    is_active: bool = True
    is_superuser: bool = False
    hashed_password: str