from datetime import datetime, timedelta, timezone
from jose import jwt
from jose import ExpiredSignatureError
from jose import JWTError
from app.config import settings
from fastapi import HTTPException
from app.utils.validator.json_validator import JsonResponse

import secrets


def create_access_token(data: dict):
    """Create an access token with expiration time.

    Args:
        data (dict): The data to be encoded in the JWT token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Calculate the expiration time in seconds from now
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    # Create the token
    access_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    return access_token, expires_in


def create_refresh_token(data: dict):
    """Create a refresh token with configurable expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    refresh_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return refresh_token, expires_in


def create_guest_access_token(data: dict):
    """Create an access token with expiration time.

    Args:
        data (dict): The data to be encoded in the JWT token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.GUEST_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Calculate the expiration time in seconds from now
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    # Create the token
    access_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    return access_token, expires_in

def verify_access_token(token: str):
    """Verify the JWT access token.

    Args:
        token (str): The JWT token to be verified.

    Returns:
        dict: The decoded payload if the token is valid.

    Raises:
        JSONResponse: If the token is missing, expired, or invalid.
    """
    if not token:
        return JsonResponse.error("User-Token is missing.", {"error": "User-Token is missing."}, status_code=401)

    try:
        # Decode the token using the secret and algorithm
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise ExpiredSignatureError("Token has expired.")

        return payload

    except ExpiredSignatureError:
        return JsonResponse.error("Access token has expired. Please login again.", {"error": "Access token has expired."}, status_code=401)
    except JWTError:
        return JsonResponse.error("Invalid token. Please provide a valid access token.", {"error": "Invalid token."}, status_code=401)
        
def create_share_token(data: dict):
    """Create a share token without expiration time.

    Args:
        data (dict): The data to be encoded in the JWT token.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    # No expiration added for share tokens
    share_token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return share_token
        
def verify_share_token(token: str):
    """Verify the share token (without expiration)."""
    if not token:
        return JsonResponse.error("Share-Token is missing.", {"error": "Share-Token is missing."}, status_code=401)
    print(f"{token}")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload  

    except JWTError:
        return JsonResponse.error("Invalid share token.", {"error": "Invalid share token."}, status_code=401)
