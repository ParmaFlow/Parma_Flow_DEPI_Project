from fastapi import APIRouter, Depends

from backend.api.schemas import AuthResponse, LoginRequest, UserProfile
from backend.api.security import authenticate_user, create_mock_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(credentials: LoginRequest) -> AuthResponse:
    user = authenticate_user(credentials)
    return AuthResponse(access_token=create_mock_token(user), user=user)


@router.get("/me", response_model=UserProfile)
def me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user




