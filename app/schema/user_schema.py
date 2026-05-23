from pydantic import BaseModel
from fastapi import HTTPException, Header
from app.config import settings


class SignupRequest(BaseModel):
    """
    Request model for user signup.

    Attributes:
        username (str): The desired username.
        email (str): User's email address.
        password (str): User's password.
    """
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """
    Request model for user login.

    Attributes:
        email (str): User's email address.
        password (str): User's password.
    """
    email: str
    password: str


class GoogleRequest(BaseModel):
    """
    Request model for Google authentication.

    Attributes:
        token (str): Google OAuth token.
    """
    token: str


def verify_BEARER_TOKEN(authorization: str = Header(None)):
    """
    Verifies that the provided Authorization header contains the correct bearer token.

    Args:
        authorization (str): The 'Authorization' HTTP header value in the format 'Bearer <token>'.

    Returns:
        None

    Raises:
        HTTPException: If the token is missing or invalid, raises 401 Unauthorized.
    """
    expected_token = settings.BEARER_TOKEN
    if not authorization or authorization != f"Bearer {expected_token}":
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authorization token"
        )
