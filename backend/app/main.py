from fastapi import FastAPI

from app.routers import users, auth, admin, pmi, web_auth, pmi_drafts, pmi_chat



app = FastAPI(
    title="PMI Platform API",
    description="Backend API for the PMI Platform",
    version="0.1.0",
)


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(pmi.router)
app.include_router(web_auth.router)
app.include_router(pmi_drafts.router)
app.include_router(pmi_chat.router)


@app.get("/")
def root():
    return {
        "message": "PMI Platform API",
        "status": "running",
    }
