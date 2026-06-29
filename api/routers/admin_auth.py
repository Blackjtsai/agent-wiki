# ============================================================
# File: admin_auth.py
# Desc: POST /admin/login — admin token validation
# Module: api/routers/
# Created: 2026-06-28
# Dev: Blackjtsai
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.config import settings

router = APIRouter(tags=["Admin - Auth"])


class LoginRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    success: bool
    message: str


@router.post("/login", response_model=LoginResponse, summary="後台登入")
async def login(request: LoginRequest) -> LoginResponse:
    """驗證 Bearer token，成功後前端自行儲存並帶入後續請求。

    Args:
        request: 含 token 的登入請求

    Returns:
        LoginResponse: success=True 表示 token 正確
    """
    if request.token != settings.secret_key:
        raise HTTPException(status_code=401, detail="Token 錯誤")

    return LoginResponse(success=True, message="登入成功")
