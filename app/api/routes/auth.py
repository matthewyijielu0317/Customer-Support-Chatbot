from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.engine import Engine

from src.config.settings import settings
from src.persistence.postgres.client import create_sync_engine
from src.persistence.postgres.queries import verify_user_credentials


router = APIRouter(tags=["auth"])

_ENGINE = create_sync_engine(settings.postgres_dsn) if settings.postgres_dsn else None


class LoginRequest(BaseModel):
    email: str
    passcode: str


class LoginResponse(BaseModel):
    success: bool
    user: dict | None = None


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    """Authenticate a user and return user details."""
    if not _ENGINE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured",
        )

    user = verify_user_credentials(
        _ENGINE, user_id=payload.email, passcode=payload.passcode
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    return LoginResponse(success=True, user=user)

