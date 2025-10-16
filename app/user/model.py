from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.interview.model import Grade


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str = Field(max_length=50, unique=True, description="로그인용")
    password: str
    role: UserRole = Field(sa_column_kwargs={"nullable": False})
    star_count: int = Field(default=0)

    # Relationships
    grades: List["Grade"] = Relationship(back_populates="user")


