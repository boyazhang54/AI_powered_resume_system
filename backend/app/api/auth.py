from fastapi import APIRouter, Depends

from app.schemas.auth import AuthRequest, AuthResponse, UserResponse
from app.services.auth import authenticate_user, create_access_token, create_user, get_current_user


router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse)
def register(payload: AuthRequest):
    user = create_user(payload.username, payload.password)
    return AuthResponse(access_token=create_access_token(user["id"], user["username"]), user=UserResponse(**user))


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest):
    user = authenticate_user(payload.username, payload.password)
    return AuthResponse(access_token=create_access_token(user["id"], user["username"]), user=UserResponse(**user))


@router.get("/auth/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return UserResponse(**user)
