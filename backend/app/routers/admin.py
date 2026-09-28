from fastapi import APIRouter, Depends

from app.configs.dependencies import require_role
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.get("/test")
def admin_test(
    current_user: User = Depends(require_role("SUPER_ADMIN"))):
    return {
        "message": "Welcome, administrator",
        "user_id": current_user.id,
        "email": current_user.email,
    }