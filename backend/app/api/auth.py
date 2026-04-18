from fastapi import APIRouter, Depends

from backend.app.auth import AuthUser, get_current_user
from backend.app.schemas.auth import AuthUserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=AuthUserResponse)
def get_me(user: AuthUser = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(username=user.username, display_name=user.display_name, role=user.role)
