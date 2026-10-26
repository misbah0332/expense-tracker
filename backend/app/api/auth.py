from fastapi import APIRouter

from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    access_token = auth_service.login(payload.username, payload.password)
    return TokenResponse(access_token=access_token, token_type="bearer")
