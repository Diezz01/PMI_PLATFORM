from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


app = FastAPI(
    title="PMI Platform API",
    description="Backend API for the PMI Platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "PMI Platform API",
        "status": "running",
    }


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.scalars(
        select(User)
    ).all()

    return users