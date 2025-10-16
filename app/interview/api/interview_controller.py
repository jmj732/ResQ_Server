from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.database import get_session
from app.interview.application.interview_service import InterviewService
from app.interview.dto.interview_dto import (
    InterviewStartRequest,
    InterviewStartResponse,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationBatchRequest,
    EvaluationBatchResponse,
    TailQuestionResponse
)
from app.auth.jwt import get_current_user
from app.user.model import User

router = APIRouter(tags=["Interview"], prefix='/interview')

@router.get('/progress', response_model=EvaluationBatchResponse, status_code=status.HTTP_200_OK)
def interview_progress(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    company_id: int = Query(..., description="Company ID to check interview progress")
):
    interview_service = InterviewService(session)
    response = interview_service.get_interview_progress(current_user.id, company_id)

    return response

@router.get('', response_model=InterviewStartResponse)
def start_interview(
    company_id: int = Query(..., description="Company ID to start interview"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Start an interview by selecting questions from the company's question pool"""
    interview_service = InterviewService(session)
    
    try:
        return interview_service.start_interview(company_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"면접 시작 중 오류가 발생했습니다: {str(e)}"
        )

@router.post('/evaluate', response_model=EvaluationBatchResponse)
def evaluate_answers_batch(
    batch_request: EvaluationBatchRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Evaluate multiple questions and answers at once (5+ including tail questions)"""
    interview_service = InterviewService(session)
    
    try:
        # 질문과 답변 개수 일치 검증
        if len(batch_request.question) != len(batch_request.answer):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="question과 answer의 개수가 일치해야 합니다."
            )
        
        # 최소 5개 이상 필요 (기본 질문 5개 + 꼬리질문)
        if len(batch_request.question) < 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="최소 5개 이상의 질문과 답변이 필요합니다."
            )
        
        # 기본 질문 개수 확인 (tail_로 시작하지 않는 질문)
        main_question_count = sum(1 for q in batch_request.question if not q.startswith("tail_"))
        if main_question_count < 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="기본 질문은 최소 5개 이상이어야 합니다."
            )
        
        return interview_service.evaluate_answers_batch(batch_request, current_user.id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"평가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get('/tail', response_model=TailQuestionResponse)
def generate_tail_question(
    company_id: int = Query(..., description="Company ID"),
    question: str = Query(..., description="Original question"),
    answer: str = Query(..., description="User's answer"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """답변을 분석하여 필요한 경우에만 꼬리질문 생성"""
    interview_service = InterviewService(session)

    try:
        return interview_service.generate_tail_question(company_id, question, answer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"꼬리질문 생성 중 오류가 발생했습니다: {str(e)}"
        )
