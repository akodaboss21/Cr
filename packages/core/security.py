"""
Security utilities for authentication and authorization
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from packages.core.config import settings
from packages.core.database import get_db
from packages.core.identity.models import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SAFE_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "https://localhost",
]

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard earlier",
    "forget all previous",
    "ignore all prior",
    "do not follow",
    "ignore these rules",
    "delete all",
    "reset your",
    "disable safety",
    "open the pod bay doors",
]


def get_client_ip(request: Request) -> str:
    """Extract client IP for rate limiting and logging"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def parse_allowed_origins() -> List[str]:
    allowed = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
    return [origin.strip() for origin in allowed if origin.strip()]


def sanitize_string(value: str) -> str:
    """Sanitize individual string input for safe storage and processing"""
    if value is None:
        return value

    if len(value) > settings.MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Input exceeds maximum allowed length"
        )

    value = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<.*?>", "", value)
    value = re.sub(r"on\w+\s*=\s*\".*?\"", "", value, flags=re.IGNORECASE)
    value = re.sub(r"on\w+\s*=\s*'.*?'", "", value, flags=re.IGNORECASE)
    value = re.sub(r"javascript:\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def sanitize_input(data: Any) -> Any:
    """Recursively sanitize JSON-compatible input values."""
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(v) for v in data]
    return data


def detect_prompt_injection(text: Optional[str]) -> bool:
    """Detect high-risk prompt injection patterns."""
    if not text:
        return False
    lowered = text.lower()
    return any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS)


def validate_prompt_messages(messages: Any) -> None:
    """Validate LLM prompt messages for dangerous content."""
    if not isinstance(messages, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages must be an array of content objects."
        )

    for message in messages:
        if not isinstance(message, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each message must be an object with role and content."
            )
        content = message.get("content")
        if detect_prompt_injection(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt content contains unsafe instructions."
            )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user record with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current authenticated user from token"""
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    organization_id: Optional[str] = payload.get("org_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if organization_id and user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token organization mismatch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user_id,
        "organization_id": organization_id,
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
        "is_admin": payload.get("is_admin", False),
    }


def require_permission(permission: str):
    """Dependency to require a specific permission"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


def require_role(role: str):
    """Dependency to require a specific role"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if role not in current_user.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return role_checker


def validate_csrf_token(request: Request) -> None:
    """Validate CSRF token for state-changing requests"""
    csrf_header = request.headers.get("x-csrf-token")
    csrf_cookie = request.cookies.get("csrf_token")
    if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )
