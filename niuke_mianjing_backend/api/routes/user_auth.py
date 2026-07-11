import re
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from pymysql.err import IntegrityError

from niuke_mianjing_backend.api.middleware.error_handler import AppException, BadRequestException, UnauthorizedException
from niuke_mianjing_backend.api.security import create_user_token, decode_user_token, hash_password, normalize_email, verify_password
from niuke_mianjing_backend.repositories.review_repo import ReviewRepository
from niuke_mianjing_backend.schemas import ApiResponse


router = APIRouter(prefix="/api/user-auth", tags=["User Authentication"])
account_repo = ReviewRepository()

DISPLAY_NAME_PREFIXES = ("星河", "清风", "远山", "晨曦", "云海", "青岚", "暖阳", "月白", "流光", "松涛")
DISPLAY_NAME_ANIMALS = ("海豚", "白鲸", "雪豹", "雨燕", "赤狐", "云雀", "灵鹿", "飞鱼", "熊猫", "海鸥")


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


def optional_user_id(x_user_token: Optional[str] = Header(None, alias="X-User-Token")) -> Optional[int]:
    return decode_user_token(x_user_token)


def require_user_id(user_id: Optional[int] = Depends(optional_user_id)) -> int:
    if not user_id:
        raise UnauthorizedException("请先登录")
    return user_id


def require_public_window(offset: int, limit: int, user_id: Optional[int], is_admin: bool = False) -> None:
    if offset + limit > 24 and not user_id and not is_admin:
        raise UnauthorizedException("登录后可继续浏览")


def _valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


def generate_display_name() -> str:
    return f"{secrets.choice(DISPLAY_NAME_PREFIXES)}{secrets.choice(DISPLAY_NAME_ANIMALS)}·{secrets.randbelow(9000) + 1000:04d}"


async def _ensure_display_name(account: dict) -> dict:
    if account.get("display_name"):
        return account
    return await account_repo.set_account_display_name(account["id"], generate_display_name())


def _session(account: dict) -> dict:
    return {
        "id": account["id"],
        "email": account["email"],
        "display_name": account["display_name"],
        "token": create_user_token(account["id"]),
    }


@router.post("/register", response_model=ApiResponse[dict])
async def register(request: RegisterRequest):
    email = normalize_email(request.email)
    if not _valid_email(email):
        raise BadRequestException("邮箱格式不正确")
    if await account_repo.get_account_by_email(email):
        raise AppException(code=409, message="该邮箱已注册")
    try:
        account = await account_repo.create_account(email, hash_password(request.password), generate_display_name())
    except IntegrityError as exc:
        raise AppException(code=409, message="该邮箱已注册") from exc
    return ApiResponse(message="注册成功", data=_session(account))


@router.post("/login", response_model=ApiResponse[dict])
async def login(request: LoginRequest):
    account = await account_repo.get_account_by_email(normalize_email(request.email))
    if not account or not verify_password(request.password, account["password_hash"]):
        raise UnauthorizedException("邮箱或密码错误")
    account = await _ensure_display_name(account)
    return ApiResponse(message="登录成功", data=_session(account))


@router.get("/me", response_model=ApiResponse[dict])
async def me(user_id: int = Depends(require_user_id)):
    account = await account_repo.get_account_by_id(user_id)
    if not account:
        raise UnauthorizedException("用户会话无效")
    account = await _ensure_display_name(account)
    return ApiResponse(
        message="会话有效",
        data={"id": account["id"], "email": account["email"], "display_name": account["display_name"]},
    )
