from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_token(data: dict[str, Any], minutes: int, token_type: str) -> tuple[str, int]:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire, "token_type": token_type})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int((expire - datetime.now(timezone.utc)).total_seconds())


def create_access_token(user_id: int, email: str, role: str) -> tuple[str, int]:
    return create_token(
        {"sub": str(user_id), "id": user_id, "email": email, "role": role},
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "access",
    )


def create_refresh_token(user_id: int, email: str, role: str) -> tuple[str, int]:
    return create_token(
        {"sub": str(user_id), "id": user_id, "email": email, "role": role},
        settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def is_token_error(exc: Exception) -> bool:
    return isinstance(exc, JWTError)
