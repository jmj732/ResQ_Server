from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.auth.jwt import get_current_user
from app.user.model import User
from app.user.application.my_service import MyService

router = APIRouter(tags=["My"], prefix='/my')

@router.get("/progress")
def get_progress(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
):
    """현재 로그인한 사용자의 진행 상황 조회 (star_count, 면접 통계)"""
    my_service = MyService(session)

    try:
        return my_service.get_user_progress(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
