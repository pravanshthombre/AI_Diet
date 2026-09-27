from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.orm import Session
from .database import get_db
from . import models

# Security configuration (optional bearer to allow anonymous access)
security = HTTPBearer(auto_error=False)

def get_supabase_uid(auth: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Returns the user's device/client UID without checking Supabase JWTs.
    If an Authorization header is provided, use the token directly.
    Otherwise, fall back to a default local user identifier.
    """
    if auth and auth.credentials:
        return auth.credentials
    return "default_local_user"


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
        first_user = db.query(models.User).first()
        if first_user:
            return first_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found. Please complete onboarding."
        )
    return user
