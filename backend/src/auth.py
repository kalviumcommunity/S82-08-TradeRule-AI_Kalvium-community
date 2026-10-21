"""
Authentication & Authorization utilities for TradeRule AI.
Includes Argon2id password hashing, JWT token handling, and FastAPI route dependencies.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

try:
    from .db import User, get_db, get_user_by_id
except ImportError:
    from db import User, get_db, get_user_by_id

# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Stable fallback for local dev if not supplied
    SECRET_KEY = "traderule-ai-local-dev-secret-key-change-in-production-min-32-chars-long"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
SESSION_COOKIE_NAME = "traderule_session"

# Determine production mode
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"} or bool(os.getenv("RENDER")) or bool(os.getenv("VERCEL"))

# Initialize Argon2 Password Hasher
password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # 19 MiB
    parallelism=1,
)


# ============================================================
# VALIDATION
# ============================================================

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_address(email: str) -> str:
    """Validate and normalize an email address."""
    email = email.strip()
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format.",
        )
    return email.lower()


def validate_password_strength(password: str) -> None:
    """Enforce minimum password security requirements."""
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )
    # Check for basic complexity (at least one letter and one number or special char)
    has_letter = any(c.isalpha() for c in password)
    has_digit_or_special = any(not c.isalpha() for c in password)
    if not (has_letter and has_digit_or_special):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain letters and numbers or symbols.",
        )


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


# ============================================================
# JWT TOKEN HANDLING
# ============================================================

def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for a user."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a signed JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
# COOKIE HELPERS
# ============================================================

def set_auth_cookie(response: Response, token: str) -> None:
    """Set HttpOnly session cookie on response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        expires=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        samesite="lax",
        secure=IS_PRODUCTION,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear session cookie on logout."""
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=IS_PRODUCTION,
    )


# ============================================================
# FASTAPI ROUTE DEPENDENCIES
# ============================================================

def extract_token_from_request(
    authorization: str | None = Header(None),
    cookie_token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> str | None:
    """Extract token from Authorization header or HttpOnly cookie."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
    cookie_token: str | None = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> User:
    """
    Authenticate the current request.
    Raises 401 if unauthenticated or invalid session.
    """
    token = extract_token_from_request(authorization, cookie_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated.",
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the authenticated user holds the admin role.
    Raises 403 Forbidden if user is not an administrator.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required for this operation.",
        )
    return current_user
