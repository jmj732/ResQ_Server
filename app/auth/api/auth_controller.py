from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlmodel import Session, select
from app.database import get_session
from app.auth.application.auth_service import AuthService
from app.auth.dto.login_dto import LoginRequest, LoginResponse, SignupRequest, SignupResponse
from app.user.model import User, UserRole
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
    response: Response,
    login_request: LoginRequest,
    session: Session = Depends(get_session)
):
    auth_service = AuthService(session)
    try:
        result = auth_service.login(login_request)

        # Refresh token은 HttpOnly 쿠키에 저장 (XSS 공격 방지)
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,      # JavaScript 접근 불가
            secure=True,        # HTTPS에서만 전송
            samesite="lax",     # CSRF 방지
            max_age=7*24*60*60  # 7일
        )

        # Access token만 응답 body에 포함 (클라이언트 메모리에 저장)
        return LoginResponse(
            access_token=result["access_token"],
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


@router.post("/refresh")
def refresh_token(
    response: Response,
    request: Request,
    session: Session = Depends(get_session)
):
    """리프레시 토큰으로 새로운 액세스 토큰 발급 (쿠키에서 refresh token 읽기)"""
    # HttpOnly 쿠키에서 refresh token 가져오기
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 없습니다."
        )

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

    # 새 refresh token을 HttpOnly 쿠키에 다시 저장
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7*24*60*60
    )

    # Access token만 body에 반환
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": user.uid
    }


@router.post("/logout")
def logout(response: Response):
    """로그아웃 (쿠키 삭제 + 클라이언트 메모리의 access token 삭제)"""
    # HttpOnly 쿠키 삭제
    response.delete_cookie(key="refresh_token")
    return {"message": "로그아웃되었습니다."}