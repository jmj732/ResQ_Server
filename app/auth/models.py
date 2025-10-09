from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text, Enum as SQLEnum
from typing import Optional, List
from enum import Enum

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


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    culture_fit: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Relationships
    interview_questions: List["InterviewQuestion"] = Relationship(back_populates="company")
    grades: List["Grade"] = Relationship(back_populates="company")


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


class InterviewQuestion(SQLModel, table=True):
    __tablename__ = "interview_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id")
    year: int
    category: Optional[str] = Field(default=None, max_length=20)
    question: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Relationships
    company: Optional["Company"] = Relationship(back_populates="interview_questions")