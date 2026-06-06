import secrets
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from niuke_mianjing_backend.api.middleware.error_handler import UnauthorizedException
from niuke_mianjing_backend.api.security import create_admin_token, is_valid_admin_token
from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.schemas import ApiResponse


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class AdminLoginRequest(BaseModel):
    api_key: str = Field(..., min_length=1)


def _is_valid_api_key(value: Optional[str]) -> bool:
    return bool(settings.API_KEY and value and secrets.compare_digest(value, settings.API_KEY))


@router.post("/login", response_model=ApiResponse[dict])
async def admin_login(request: AdminLoginRequest):
    if not _is_valid_api_key(request.api_key):
        raise UnauthorizedException("管理员密钥不正确")
    return ApiResponse(message="登录成功", data={"authenticated": True, "token": create_admin_token()})


@router.get("/me", response_model=ApiResponse[dict])
async def admin_session(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not is_valid_admin_token(x_admin_token):
        raise UnauthorizedException("管理员会话无效")
    return ApiResponse(message="会话有效", data={"authenticated": True})
