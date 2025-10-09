from fastapi import Response


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """인증 토큰을 HttpOnly 쿠키에 저장"""
    # 액세스 토큰 (15분)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # 개발환경: False, 프로덕션(HTTPS): True
        samesite="lax",
        max_age=15 * 60
    )

    # 리프레시 토큰 (7일)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # 개발환경: False, 프로덕션(HTTPS): True
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )


def clear_auth_cookies(response: Response) -> None:
    """인증 토큰 쿠키 삭제"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
