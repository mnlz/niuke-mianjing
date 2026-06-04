from fastapi import Request
from fastapi.responses import JSONResponse
from niuke_mianjing_backend.schemas.response import ApiResponse


class AppException(Exception):
    def __init__(self, code: int = 500, message: str = "Internal Server Error", data=None):
        self.code = code
        self.message = message
        self.data = data


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", data=None):
        super().__init__(code=404, message=message, data=data)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", data=None):
        super().__init__(code=400, message=message, data=data)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", data=None):
        super().__init__(code=401, message=message, data=data)


async def app_exception_handler(request: Request, exc: AppException):
    response = ApiResponse(code=exc.code, message=exc.message, data=exc.data)
    return JSONResponse(status_code=exc.code, content=response.model_dump())


async def generic_exception_handler(request: Request, exc: Exception):
    response = ApiResponse(code=500, message=f"Internal Server Error: {str(exc)}", data=None)
    return JSONResponse(status_code=500, content=response.model_dump())
