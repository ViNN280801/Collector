from __future__ import annotations

import secrets
import time
from typing import Any, Dict, Optional, Union, cast

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_SCHEME = HTTPBearer(auto_error=False)


class APIKeyAuth:
    def __init__(self, api_keys: Optional[Dict[str, str]] = None) -> None:
        self._api_keys: Dict[str, str] = api_keys or {}
        self._key_to_name: Dict[str, str] = {}

        for name, key in self._api_keys.items():
            self._key_to_name[key] = name

    def add_key(self, name: str, key: str) -> None:
        self._api_keys[name] = key
        self._key_to_name[key] = name

    def remove_key(self, name: str) -> None:
        if name in self._api_keys:
            key = self._api_keys[name]
            del self._api_keys[name]
            if key in self._key_to_name:
                del self._key_to_name[key]

    def validate_key(self, api_key: Optional[str]) -> bool:
        if not api_key:
            return False
        return api_key in self._key_to_name

    def get_key_name(self, api_key: str) -> Optional[str]:
        return self._key_to_name.get(api_key)

    async def verify_api_key(self, api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
        if not self.validate_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
        if api_key is None:
            return "unknown"
        return self.get_key_name(api_key) or "unknown"


class JWTAuth:
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256") -> None:
        self._secret_key = secret_key or secrets.token_urlsafe(32)
        self._algorithm = algorithm
        self._tokens: Dict[str, Dict[str, Any]] = {}

    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        import jwt

        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        token: Union[str, bytes] = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        # jwt.encode returns str in PyJWT 2.0+, but mypy sees it as Any
        if isinstance(token, bytes):
            token_str = token.decode("utf-8")
        else:
            token_str = token  # already str
        self._tokens[token_str] = {"user_id": user_id, "expires_at": payload["exp"]}
        return token_str

    def validate_token(self, token: str) -> Optional[str]:
        import jwt

        if token in self._tokens:
            token_data = self._tokens[token]
            if token_data["expires_at"] > time.time():
                cached_user_id = cast(Optional[str], token_data.get("user_id"))
                if cached_user_id:
                    return cached_user_id

        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            decoded_user_id: Optional[str] = payload.get("user_id")
            if decoded_user_id:
                self._tokens[token] = {"user_id": decoded_user_id, "expires_at": payload["exp"]}
            return decoded_user_id
        except jwt.ExpiredSignatureError:
            if token in self._tokens:
                del self._tokens[token]
            return None
        except jwt.InvalidTokenError:
            return None

    async def verify_token(self, credentials: Any = Security(BEARER_SCHEME)) -> str:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials if hasattr(credentials, "credentials") else str(credentials)
        user_id = self.validate_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    def revoke_token(self, token: str) -> None:
        if token in self._tokens:
            del self._tokens[token]


class AuthManager:
    def __init__(
        self,
        api_keys: Optional[Dict[str, str]] = None,
        jwt_secret: Optional[str] = None,
        require_auth: bool = False,
    ) -> None:
        self._api_key_auth = APIKeyAuth(api_keys)
        self._jwt_auth = JWTAuth(jwt_secret)
        self._require_auth = require_auth

    def get_api_key_auth(self) -> APIKeyAuth:
        return self._api_key_auth

    def get_jwt_auth(self) -> JWTAuth:
        return self._jwt_auth

    def is_auth_required(self) -> bool:
        return self._require_auth

    def set_require_auth(self, require: bool) -> None:
        self._require_auth = require
