from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    from app.auth.models import User, Company, Grade, Feedback, Strength, InterviewQuestion
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session