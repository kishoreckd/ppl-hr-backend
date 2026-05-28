from fastapi import HTTPException, Request
from app.utils.validator.json_validator import JsonResponse


def success(message: str, data=None, status_code: int = 200):
    return JsonResponse.success(message, data if data is not None else {}, status_code=status_code)


def error(message: str, errors=None, status_code: int = 400):
    return JsonResponse.error(message, errors or [], status_code=status_code)


async def http_exception_handler(request: Request, exc: HTTPException):
    return JsonResponse.error(str(exc.detail), status_code=exc.status_code)


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JsonResponse.error("Internal server error", [str(exc)], status_code=500)
