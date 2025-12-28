from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import AuthManager
from .routes import get_auth_manager

router = APIRouter(prefix="/api/v1/auth")


@router.post("/token")
async def generate_token(
    user_id: str,
    expires_in: int = 3600,
    auth_manager: Optional[AuthManager] = Depends(get_auth_manager),
) -> Dict[str, Any]:
    if not auth_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )

    jwt_auth = auth_manager.get_jwt_auth()
    token = jwt_auth.generate_token(user_id, expires_in)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user_id": user_id,
    }


@router.post("/api-key")
async def create_api_key(
    name: str,
    auth_manager: Optional[AuthManager] = Depends(get_auth_manager),
) -> Dict[str, Any]:
    if not auth_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )

    import secrets

    api_key = secrets.token_urlsafe(32)
    api_key_auth = auth_manager.get_api_key_auth()
    api_key_auth.add_key(name, api_key)

    return {
        "name": name,
        "api_key": api_key,
        "message": "Save this API key securely. It will not be shown again.",
    }
