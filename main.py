from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.auth.api.auth_controller import router as auth_router
from app.user.api.my_controller import router as my_router
from app.question.api.question_controller import router as question_router
from app.interview.api.interview_controller import router as interview_router
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)


app = FastAPI(title="Interview API", version="1.0.0", lifespan=lifespan)

# CORS: allow all origins, methods, headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(my_router)
app.include_router(question_router)
app.include_router(interview_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)