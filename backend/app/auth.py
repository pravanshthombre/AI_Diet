from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from sqlalchemy.orm import Session
from .database import get_db
from . import models

# Security configuration
security = HTTPBearer()
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"

def get_supabase_uid(auth: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decodes the Supabase JWT and returns the user's Supabase UID.
    Does not check the database, making it safe for onboarding endpoints.
    """
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: SUPABASE_JWT_SECRET not set."
        )

    token = auth.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        supabase_uid = payload.get("sub")
        if not supabase_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject claim."
            )
        return supabase_uid
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )


def get_current_user(
    supabase_uid: str = Depends(get_supabase_uid),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency that verifies the Supabase JWT and returns the internal User model.
    Rejects the request if the user is not found in the database.
    """
    user = db.query(models.User).filter(models.User.supabase_uid == supabase_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found. Please complete onboarding."
        )
    return user
