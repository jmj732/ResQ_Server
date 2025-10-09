import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.database import engine
from app.auth.application.auth_service import AuthService

def create_test_user():
    with Session(engine) as session:
        auth_service = AuthService(session)
        try:
            user = auth_service.create_user("dohun08", "q1w2e3")
            print(f"Test user created: {user.user_id}")
        except Exception as e:
            print(f"User creation failed or user already exists: {e}")

if __name__ == "__main__":
    create_test_user()