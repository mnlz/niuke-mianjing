from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.api.security import is_valid_admin_token


class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_EXACT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/login",
        "/api/user-auth/register",
        "/api/user-auth/login",
        "/api/user-auth/me",
        "/api/logs/stats",
        "/api/logs/filters",
        "/api/logs/data",
        "/api/review/progress",
        "/api/review/overview",
        "/api/recruitment/sources",
        "/api/recruitment/tracks",
        "/api/recruitment/recruitment-types",
        "/api/recruitment/jobs",
        "/api/recruitment/job-interviews",
        "/api/recruitment/track-interviews",
        "/api/recruitment/resume/parse",
        "/api/recruitment/ai-report",
        "/api/recruitment/ai-reports",
    }
    PUBLIC_PREFIXES = (
        "/api/logs/data/",
        "/api/review/progress/",
        "/api/recruitment/ai-reports/",
    )

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)
        if path in self.PUBLIC_EXACT_PATHS or any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES):
            return await call_next(request)

        if not settings.API_KEY:
            return JSONResponse(
                status_code=503,
                content={"code": 503, "message": "后台 API_KEY 尚未配置", "data": None},
            )

        if not is_valid_admin_token(request.headers.get("X-Admin-Token")):
            return JSONResponse(
                status_code=401,
                content={"code": 401, "message": "需要管理员登录", "data": None},
            )

        return await call_next(request)
