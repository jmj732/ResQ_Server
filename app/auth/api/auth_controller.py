from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.auth.application.auth_service import AuthService
from app.auth.dto.login_dto import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from app.auth.models import User, UserRole
from app.auth.jwt import (
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_active_admin,
)

router = APIRouter(tags=["Authentication"], prefix='/auth')

@router.post("/login", response_model=LoginResponse, status_code=200)
def login(
    login_request: LoginRequest,
    session: Session = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        result = auth_service.login(login_request)

        # 토큰을 응답 body에 포함
        return LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer",
            user_id=result["user_id"],
            role=result["role"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(
    signup_request: SignupRequest,
    session: Session = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        # role 문자열을 UserRole enum으로 변환
        user_role = UserRole.ADMIN if signup_request.role == "ADMIN" else UserRole.USER

        user = auth_service.create_user(
            user_id=signup_request.user_id,
            password=signup_request.password,
            role=user_role
        )
        return SignupResponse(
            message="회원가입에 성공했습니다.",
            user_id=user.uid
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인된 사용자 정보 조회 (JWT 인증 필요)"""
    return {
        "user_id": current_user.uid,
        "role": current_user.role.value,
        "star_count": current_user.star_count
    }


@router.get("/admin-only")
def admin_only(current_user: User = Depends(get_current_active_admin)):
    """관리자 전용 엔드포인트 예제"""
    return {
        "message": "관리자 페이지에 오신 것을 환영합니다!",
        "admin": current_user.uid
    }


@router.post("/refresh")
def refresh_token(
    refresh_token: str,
    session: Session = Depends(get_session)
):
    """리프레시 토큰으로 새로운 액세스 토큰 발급"""
    # 리프레시 토큰 검증
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다."
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다."
        )

    # DB에서 사용자 확인
    statement = select(User).where(User.uid == user_id)
    user = session.exec(statement).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다."
        )

    # 새로운 액세스 토큰 및 리프레시 토큰 발급
    token_data = {"sub": user.uid, "role": user.role.value}
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": user.uid
    }


@router.post("/logout")
def logout():
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return {"message": "로그아웃되었습니다."}