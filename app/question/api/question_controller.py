from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlmodel import Session

from app.database import get_session
from app.question.application.question_service import QuestionService
from app.question.dto.question_dto import (
    QuestionResponse,
    QuestionAdditionResponse,
    QuestionAdditionRequest,
    QuestionUpdateRequest,
    QuestionUpdateResponse,
    QuestionDeleteResponse
)
from app.common.dto.page_dto import Page, Pageable
from app.auth.jwt import get_current_active_admin
from app.user.model import User
from typing import Optional

router = APIRouter(tags=["Question"], prefix='/question')


@router.get("/search", response_model=Page[QuestionResponse])
def search_questions(
    company_id: Optional[int] = Query(None, description="Company ID filter"),
    year: Optional[int] = Query(None, description="Year filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Search interview questions with pagination (ADMIN only)"""
    question_service = QuestionService(session)

    pageable = Pageable(page=page, size=size)

    return question_service.search_questions(
        company_id=company_id,
        year=year,
        category=category,
        pageable=pageable
    )


@router.post("/addition", response_model=QuestionAdditionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    question_request: QuestionAdditionRequest,
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Add a new interview question (ADMIN only)"""
    question_service = QuestionService(session)

    try:
        return question_service.add_question(
            company_id=question_request.company_id,
            year=question_request.year,
            category=question_request.category,
            question=question_request.question
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/update", response_model=QuestionUpdateResponse)
def update_question(
    update_request: QuestionUpdateRequest,
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Update an interview question's content (ADMIN only)"""
    question_service = QuestionService(session)

    try:
        return question_service.update_question(
            question_id=update_request.question_id,
            content=update_request.content
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/delete/{question_id}", response_model=QuestionDeleteResponse)
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Delete an interview question by ID (ADMIN only)"""
    question_service = QuestionService(session)

    try:
        return question_service.delete_question(question_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/companies", response_model=list[dict])
def get_companies(
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Get all companies with their IDs and names (ADMIN only)"""
    question_service = QuestionService(session)
    companies = question_service.get_companies()
    return [{"id": company.id, "name": company.name} for company in companies]



@router.get("/sample-file", response_class=Response)
def download_sample_file(
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Download sample Excel file for bulk question upload (ADMIN only)"""
    
    question_service = QuestionService(session)
    
    excel_content = question_service.create_sample_excel()
    
    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=question_upload_sample.xlsx"
        }
    )


@router.post("/bulk-upload")
def bulk_upload_questions(
    file: UploadFile = File(..., description="Excel file with questions"),
    current_user: User = Depends(get_current_active_admin),
    session: Session = Depends(get_session)
):
    """Upload multiple questions from Excel file (ADMIN only)"""
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Read file content
        file_content = file.file.read()
        
        question_service = QuestionService(session)
        results = question_service.bulk_upload_questions(file_content, file.filename)
        
        return {
            "message": "Upload completed",
            "total_rows": results["total_rows"],
            "success_count": results["success_count"],
            "error_count": results["error_count"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing error: {str(e)}"
        )
    finally:
        file.file.close()
