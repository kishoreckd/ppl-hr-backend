from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, current_user, to_dict
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.hr import RefreshToken, RoleEnum, User
from app.schema.hr_schema import LoginRequest, RefreshTokenRequest, ResetPasswordRequest, SignupRequest

router = APIRouter()


def public_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.post("/signup", status_code=201)
def signup(request: SignupRequest, db: Session = Depends(get_session)):
    email = request.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(name=request.name, email=email, hashed_password=hash_password(request.password), role=RoleEnum(request.role.value))
    db.add(user)
    db.flush()
    access_token, expires_in = create_access_token(user.id, user.email, user.role.value)
    refresh_token, refresh_expires_in = create_refresh_token(user.id, user.email, user.role.value)
    db.add(RefreshToken(user_id=user.id, token=refresh_token))
    audit(db, user.id, "signup", "User", str(user.id))
    db.commit()
    return success(
        "User created successfully",
        {
            "user": public_user(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "refresh_expires_in": refresh_expires_in,
        },
        status_code=201,
    )


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_session)):
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    access_token, expires_in = create_access_token(user.id, user.email, user.role.value)
    refresh_token, refresh_expires_in = create_refresh_token(user.id, user.email, user.role.value)
    db.add(RefreshToken(user_id=user.id, token=refresh_token))
    db.commit()
    return success(
        "Login successful",
        {
            "user": public_user(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "refresh_expires_in": refresh_expires_in,
        },
    )


@router.post("/refresh")
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_session)):
    try:
        payload = decode_token(request.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token type")
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == request.refresh_token, RefreshToken.revoked.is_(False)))
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    user = db.get(User, int(payload["id"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token, expires_in = create_access_token(user.id, user.email, user.role.value)
    return success("Token refreshed successfully", {"access_token": access_token, "expires_in": expires_in})


@router.post("/logout")
def logout(request: RefreshTokenRequest, db: Session = Depends(get_session), user: User = Depends(current_user)):
    token = db.scalar(select(RefreshToken).where(RefreshToken.token == request.refresh_token, RefreshToken.user_id == user.id))
    if token:
        token.revoked = True
    db.commit()
    return success("Logged out successfully")


@router.post("/forgot-password")
def forgot_password():
    return success("Forgot password flow placeholder accepted")


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    return success("Reset password flow placeholder accepted", {"token_received": bool(request.token)})


@router.post("/microsoft")
def microsoft_login():
    return success("Microsoft login placeholder accepted")


@router.get("/me")
def me(user: User = Depends(current_user)):
    return success("Current user fetched successfully", public_user(user))
