# ============================================================
# File: dependencies.py
# Desc: FastAPI shared dependencies (auth token validation)
# Module: api/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.config import settings

_bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """Validates Bearer token for admin API access.

    Raises:
        HTTPException 401: if token is missing or invalid
    """
    if credentials is None or credentials.credentials != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 Token，請重新登入",
            headers={"WWW-Authenticate": "Bearer"},
        )
