from sqlmodel import SQLModel
from typing import Optional

class LoginRequest(SQLModel):
    user_id: str
    password: str

class LoginResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str

class SignupRequest(SQLModel):
    user_id: str
    password: str
    role: Optional[str] = "USER"  # USER 또는 ADMIN

class SignupResponse(SQLModel):
    message: str
    user_id: str