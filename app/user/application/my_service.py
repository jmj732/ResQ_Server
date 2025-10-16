from sqlmodel import Session
from app.user.model import User


class MyService:
    def __init__(self, session: Session):
        self.session = session

    def get_user_progress(self, user_id: int):
        """Get user progress including star_count and interview statistics"""
        user = self.session.get(User, user_id)

        if user is None:
            raise ValueError("User not found")

        return {
            "star_count": user.star_count,
        }
