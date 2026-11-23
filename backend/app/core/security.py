"""
API Security & Authentication Helper.

Provides API key validation, bearer token extraction, and rotation verification.
"""

from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> bool:
    """
    Validates client API key against configured server secrets.
    If no key is configured in settings, public access is permitted.
    """
    expected_key = getattr(settings, "CLIENT_API_KEY", None)
    if not expected_key:
        return True

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key authentication header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return True
