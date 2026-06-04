from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from niuke_mianjing_backend.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = ["/", "/health", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next):
        if not settings.API_KEY:
            return await call_next(request)

        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        if request.url.path.startswith("/api/ws"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API Key")

        return await call_next(request)
