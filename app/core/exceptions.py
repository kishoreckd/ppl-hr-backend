from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def success(message: str, data=None):
    return {"success": True, "message": message, "data": data if data is not None else {}}


def error(message: str, errors=None):
    return {"success": False, "message": message, "errors": errors or []}


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=error(str(exc.detail)))


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error("Internal server error", [str(exc)]))
