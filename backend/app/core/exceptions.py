from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logger import logger

class VocentraException(Exception):
    def __init__(self, message: str, status_code: int = 400, data: any = None):
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)

class AuthError(VocentraException):
    def __init__(self, message: str = "Authentication failed", data: any = None):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, data=data)

class NotFoundError(VocentraException):
    def __init__(self, message: str = "Resource not found", data: any = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, data=data)

class ValidationError(VocentraException):
    def __init__(self, message: str = "Validation failed", data: any = None):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, data=data)

class ForbiddenError(VocentraException):
    def __init__(self, message: str = "Access forbidden", data: any = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, data=data)

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(VocentraException)
    async def vocentra_exception_handler(request: Request, exc: VocentraException):
        logger.error(f"Application error: {exc.message} (status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": exc.data
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP validation error: {exc.detail} (status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": str(exc.detail),
                "data": None
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        logger.warning(f"FastAPI request validation error: {errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Input validation fields failed.",
                "data": errors
            }
        )
