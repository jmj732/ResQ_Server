from fastapi import FastAPI
from app.auth.api.auth_controller import router as auth_router
from app.database import create_db_and_tables

app = FastAPI(title="Interview API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)