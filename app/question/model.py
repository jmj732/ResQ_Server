from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.interview.model import Grade


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    culture_fit: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Relationships
    interview_questions: List["InterviewQuestion"] = Relationship(back_populates="company")
    grades: List["Grade"] = Relationship(back_populates="company")


class InterviewQuestion(SQLModel, table=True):
    __tablename__ = "interview_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    year: int
    category: Optional[str] = Field(default=None, max_length=20)
    question: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Relationships
    company: Optional["Company"] = Relationship(back_populates="interview_questions")