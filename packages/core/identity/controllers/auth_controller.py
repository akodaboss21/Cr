from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.identity.schemas import LoginRequest, RefreshTokenRequest, Token
from packages.core.security import authenticate_user, create_access_token, create_refresh_token, decode_token

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": user.id,
        "org_id": user.organization_id,
        "roles": [],
        "permissions": [],
        "is_admin": getattr(user, "is_admin", False),
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": payload.get("sub"),
        "org_id": payload.get("org_id"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
        "is_admin": payload.get("is_admin", False),
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
