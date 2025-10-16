from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.user.model import User
    from app.question.model import Company


class Grade(SQLModel, table=True):
    __tablename__ = "grades"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    user_id: int = Field(foreign_key="users.id")
    value: float = Field(description="질문 별 점수의 평균")
    evaluation: str = Field(sa_column=Column(Text))

    # Relationships
    company: Optional["Company"] = Relationship(back_populates="grades")
    user: Optional["User"] = Relationship(back_populates="grades")
    feedbacks: List["Feedback"] = Relationship(back_populates="grade")
    strengths: List["Strength"] = Relationship(back_populates="grade")


class Feedback(SQLModel, table=True):
    __tablename__ = "feedbacks"

    id: Optional[int] = Field(default=None, primary_key=True)
    grade_id: int = Field(foreign_key="grades.id")
    text: str = Field(sa_column=Column(Text))

    # Relationships
    grade: Optional["Grade"] = Relationship(back_populates="feedbacks")


class Strength(SQLModel, table=True):
    __tablename__ = "strengths"

    id: Optional[int] = Field(default=None, primary_key=True)
    grade_id: int = Field(foreign_key="grades.id")
    text: str = Field(sa_column=Column(Text))

    # Relationships
    grade: Optional["Grade"] = Relationship(back_populates="strengths")

