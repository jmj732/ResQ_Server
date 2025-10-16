from sqlmodel import SQLModel
from typing import Optional, List


class QuestionSearchRequest(SQLModel):
    """Interview question search filters"""
    company_id: Optional[int] = None
    year: Optional[int] = None
    category: Optional[str] = None


class QuestionResponse(SQLModel):
    """Interview question response"""
    id: int
    company_id: int
    company_name: str
    year: int
    category: Optional[str]
    question: Optional[str]


class QuestionListResponse(SQLModel):
    """List of interview questions"""
    total: int
    questions: List[QuestionResponse]

class QuestionAdditionRequest(SQLModel):
    """Request to add a new interview question"""
    company_id: int
    year: int
    category: Optional[str] = None
    question: Optional[str] = None

class QuestionAdditionResponse(SQLModel):
    """Response after adding a new interview question"""
    question_id: int

class QuestionUpdateRequest(SQLModel):
    """Request to update an interview question"""
    question_id: int
    content: str

class QuestionUpdateResponse(SQLModel):
    """Response after updating an interview question"""
    message: str

class QuestionDeleteResponse(SQLModel):
    """Response after deleting an interview question"""
    message: str


class BulkQuestionUploadRequest(SQLModel):
    """Bulk question upload result"""
    total_rows: int
    success_count: int
    error_count: int
    errors: List[dict] = []

class QuestionUploadRow(SQLModel):
    """Single row from uploaded file"""
    company_id: int
    year: int
    category: Optional[str] = None
    question: Optional[str] = None
