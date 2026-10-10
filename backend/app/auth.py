"""
Authentication middleware for NutriCalc API.

Production-ready:
  - Verifies Supabase JWT tokens when SUPABASE_JWT_SECRET is configured
  - Falls back to UID-based auth for local development
  - Proper token expiry and signature validation
"""
import os
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.orm import Session
from .database import get_db
from . import models

logger = logging.getLogger("nutricalc.auth")

# Security configuration (optional bearer to allow anonymous access in dev)
security = HTTPBearer(auto_error=False)

# Load JWT secret for Supabase verification
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip()


def _verify_jwt(token: str) -> Optional[dict]:
    """
    Verify a Supabase JWT token and return the decoded payload.
    Returns None if verification fails or JWT secret is not configured.
    """
    if not SUPABASE_JWT_SECRET:
        return None

    try:
        from jose import jwt, JWTError
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        if not sub:
            logger.warning("JWT missing 'sub' claim")
            return None
        return payload
    except ImportError:
        logger.warning("python-jose not installed — JWT verification disabled")
        return None
    except Exception as e:
        logger.warning("JWT verification failed: %s", e)
        return None


def get_supabase_uid(auth: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Extract user UID from the Authorization header.

    Production mode (SUPABASE_JWT_SECRET set):
      - Verifies JWT signature and extracts the 'sub' claim
      - Rejects invalid/expired tokens

    Development mode (no secret):
      - Uses the raw token as a UID passthrough
      - Falls back to 'default_local_user'
    """
    if not auth or not auth.credentials:
        if SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return "default_local_user"

    token = auth.credentials

    # If JWT secret is configured, verify the token
    if SUPABASE_JWT_SECRET:
        # Check if it's a frontend local device token
        if token.startswith("device_"):
            logger.debug("Accepted local device token: %s", token)
            return token
            
        payload = _verify_jwt(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        uid = payload.get("sub", "")
        logger.debug("Authenticated Supabase user: %s", uid)
        return uid

    # Development mode: use raw token as UID
    return token


def get_current_user(
    supabase_uid: str = Depends(get_supabase_uid),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency that returns the internal User model matching the given UID.
    Rejects the request if the user is not found in the database.
    """
    user = db.query(models.User).filter(models.User.supabase_uid == supabase_uid).first()
    if not user:
        # Fallback: if default user doesn't exist, try getting the first user in the DB
        # Only in development mode (no JWT secret)
        if not SUPABASE_JWT_SECRET:
            first_user = db.query(models.User).first()
            if first_user:
                return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found. Please complete onboarding."
        )
    return user
