from sqlmodel import Session, select
from app.auth.models import User, UserRole
from app.auth.dto.login_dto import LoginRequest, LoginResponse
from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.security import verify_password, get_password_hash

class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def login(self, login_request: LoginRequest) -> dict:
        statement = select(User).where(User.uid == login_request.user_id)
        user = self.session.exec(statement).first()

        if user is None:
            raise ValueError("유저ID나 비밀번호가 올바르지 않습니다.")

        # 비밀번호 검증
        if not verify_password(login_request.password, user.password):
            raise ValueError("유저ID나 비밀번호가 올바르지 않습니다.")

        # JWT 토큰 생성 (액세스 + 리프레시)
        token_data = {"sub": user.uid, "role": user.role.value}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.uid,
            "role": user.role.value
        }

    def create_user(self, user_id: str, password: str, role: UserRole = UserRole.USER) -> User:
        statement = select(User).where(User.uid == user_id)
        existing_user = self.session.exec(statement).first()
        if existing_user:
            raise ValueError("User ID already exists")

        hashed_password = get_password_hash(password)
        user = User(uid=user_id, password=hashed_password, role=role)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user