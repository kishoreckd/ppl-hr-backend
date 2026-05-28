# app/utils/json_response.py

import json
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

class JsonResponse:
    @staticmethod
    def create(status: str, message: str, data, status_code: int, headers=None) -> JSONResponse:
        """
        Generate a standardized FastAPI JSONResponse.

        Args:
            status (str): "success" or "error"
            message (str): A descriptive message about the response
            data (any): Additional data, can be dict, list, str, etc.
            status_code (int): HTTP status code
            headers (dict, optional): Custom headers to include in the response

        Returns:
            JSONResponse: FastAPI JSONResponse object
        """
        body = {
            "status": status,
            "message": message,
            "data": data
        }
        return JSONResponse(
            content=jsonable_encoder(body),
            status_code=status_code,
            headers=headers
        )

    @classmethod
    def success(cls, message: str, data=None, status_code: int = 200, headers=None) -> JSONResponse:
        return cls.create("success", message, data, status_code, headers=headers)

    @classmethod
    def error(cls, message: str, data=None, status_code: int = 400, headers=None) -> JSONResponse:
        return cls.create("error", message, data, status_code, headers=headers)

    @classmethod
    def validation_error(cls, ve: ValidationError, status_code: int = 422, headers=None) -> JSONResponse:
        errors = []
        for err in ve.errors():
            location = " -> ".join(str(loc) for loc in err['loc'])
            errors.append({
                "field": location,
                "message": err['msg'],
                "error_type": err['type']
            })

        return cls.error(
            message="Validation error",
            data=errors,
            status_code=status_code,
            headers=headers
        )
