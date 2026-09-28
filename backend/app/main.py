from fastapi import FastAPI

from app.routers import users
from app.routers import auth
from app.routers import admin


app = FastAPI(
    title="PMI Platform API",
    description="Backend API for the PMI Platform",
    version="0.1.0",
)


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "message": "PMI Platform API",
        "status": "running",
    }