from fastapi import FastAPI, HTTPException, Depends, Header, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from datetime import datetime
from app.models.user import UserModel
from app.services.auth import hash_password, authenticate_user
from app.database import get_db
from app.config import settings
from typing import Optional
from uuid import uuid4
from app.schema.user_schema import (SignupRequest, LoginRequest, verify_BEARER_TOKEN)
from app.utils.jwt import verify_access_token, create_access_token,create_share_token,create_guest_access_token
from bson import ObjectId
from app.config import settings 

CLIENT_ID = "1061350659505-e6v1615s1ueb62tfd27jr8jhja0ooqof.apps.googleusercontent.com"


router = APIRouter()

# Google Login Request Model
class GoogleLoginRequest(BaseModel):
    token: str

# Google Login Endpoint
@router.post("/auth/google")
async def google_login(request: GoogleLoginRequest, db=Depends(get_db)):
    """
    Authenticate a user using Google OAuth and store in DB.

    Args:
        request (GoogleLoginRequest): The request containing the Google token.
        db (AsyncIOMotorDatabase): MongoDB database dependency.

    Returns:
        JSONResponse: Access and share tokens on successful authentication.

    Raises:
        HTTPException: If token is invalid or database operations fail.
    """
    print(f"requesy:{request}")
    try:
        # Verify Google Token
        idinfo = id_token.verify_oauth2_token(request.token, Request(), CLIENT_ID)

        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google account")

        # Check if user exists
        existing_user = await db["users"].find_one({"email": email})

        if existing_user:
            if not existing_user.get("google_auth"):
                # Convert the existing password-based account to Google authentication
                update_data = {
                    "$set": {
                        "google_auth": True,
                        "profile_picture": picture or existing_user.get("profile_picture"),
                        "updated_at": datetime.utcnow(),
                    },
                    "$unset": {"password": ""}  
                }

                update_result = await db["users"].update_one({"email": email}, update_data)
                if update_result.modified_count == 0:
                    raise HTTPException(status_code=500, detail="Failed to update user")

            # Generate JWT for existing (or updated) user
            token, expires_in = create_access_token({"sub": email, "id": str(existing_user["_id"])})
            share_token = create_share_token({"sub": email, "id": str(existing_user["_id"])}) 

           
        else:
            # Create new Google user
            user = UserModel(
                username=name,
                email=email,
                password=None,
                google_auth=True,  # Mark as Google authenticated
                profile_picture=picture,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            result = await db["users"].insert_one(user.dict(by_alias=True))
            if not result.acknowledged:
                raise HTTPException(status_code=500, detail="User could not be created")

            user_data = user.dict(by_alias=True)
            user_data["_id"] = str(result.inserted_id)

            # Generate JWT token
            token, expires_in = create_access_token({"sub": email, "id": user_data["_id"]})
            share_token = create_share_token({"sub": email, "id": user_data["_id"]}) 


        return JSONResponse(
            content={
                "status": "success",
                "message": "Google login successful.",
                "data": {
                    "access_token": token,
                    "share_token": share_token,
                    "expires_in": expires_in,
                },
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    
@router.post("/check/google")
async def google_login(request: GoogleLoginRequest, db=Depends(get_db)):
    """
    Generate guest access token using Google OAuth token.

    Args:
        request (GoogleLoginRequest): The request containing the Google token.
        db (AsyncIOMotorDatabase): MongoDB database dependency.

    Returns:
        JSONResponse: Guest token and basic user info.

    Raises:
        HTTPException: If token is invalid.
    """
    print(f"request:{request}")
    try:
        # Verify Google Token
        idinfo = id_token.verify_oauth2_token(request.token, Request(), CLIENT_ID)

        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google account")
        # Generate JWT token for the Google authenticated user
        token, expires_in = create_guest_access_token({"sub": email}) 
    
        # Corrected "userdata" dictionary with correct key names
        return JSONResponse(
            content={
                "status": "success",
                "message": "Google login successful.",
                "data": {
                    "guest_token": token,
                    "userdata": {'email': email, 'name': name},
                    "expires_in": expires_in,
                },
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    
    
# Updated User Signup
@router.post("/signup", dependencies=[Depends(verify_BEARER_TOKEN)])
async def signup(request: SignupRequest, db=Depends(get_db)):
    """
    Register a new user.

    Args:
        request (SignupRequest): Signup form with username, email, password.
        db (AsyncIOMotorDatabase): MongoDB database dependency.

    Returns:
        JSONResponse: Success message with access and share tokens.

    Raises:
        HTTPException: If email already exists or input validation fails.
    """
    try:
        username = request.username
        email = request.email
        password = request.password

        if not username or not email or not password:
            raise HTTPException(status_code=400, detail="Missing fields")

        password_hash = hash_password(password)

        existing_user = await db["users"].find_one({"email": email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        user = UserModel(
            username=username,
            email=email,
            password=password_hash,
            google_auth=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await db["users"].insert_one(user.dict(by_alias=True))
        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="User could not be created")
        print(f"user{user}")

        token, expires_in = create_access_token({"sub": user.email, "id": str(user.id)})
        share_token = create_share_token({"sub": user.email, "id": str(user.id)})

        return JSONResponse(
            content={
                "status": "success",
                "message": "User created successfully.",
                "data": {
                    "access_token": token,
                    "share_token": share_token, 
                    "expires_in": expires_in,  
                },
            }
        )

    except ValueError as ve:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(ve)})

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"An error occurred: {str(e)}"})

# Updated User Login
@router.post("/login", dependencies=[Depends(verify_BEARER_TOKEN)])
async def login(request: LoginRequest, db=Depends(get_db)):
    """
    Authenticate user and return access tokens.

    Args:
        request (LoginRequest): Login form with email and password.
        db (AsyncIOMotorDatabase): MongoDB database dependency.

    Returns:
        JSONResponse: Tokens and login status.

    Raises:
        HTTPException: For invalid credentials or missing fields.
    """
    try:
        email = request.email
        password = request.password

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        user = await authenticate_user(db, email, password)
        if not user:
            user_check = await db["users"].find_one({"email": email})
            if not user_check:
                raise HTTPException(status_code=401, detail="Email is invalid")
            else:
                raise HTTPException(status_code=401, detail="Incorrect password")

        token, expires_in = create_access_token({"sub": user["email"], "id": str(user["_id"])})
        share_token = create_share_token({"sub": user["email"], "id": str(user["_id"])}) 


        return JSONResponse(
            content={
                "status": "success",
                "message": "Login successful.",
                "data": {
                    "access_token": token,
                    "share_token": share_token, 
                    "expires_in": expires_in,

                },
            }
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"An error occurred: {str(e)}"})

# Updated Profile Endpoint
@router.get("/profile", dependencies=[Depends(verify_BEARER_TOKEN)])
async def user_profile(User_Token: str = Header(None), db=Depends(get_db)):
    """
    Fetch authenticated user's profile from token.

    Args:
        User_Token (str): JWT token from the request header.
        db (AsyncIOMotorDatabase): MongoDB database dependency.

    Returns:
        JSONResponse: User profile data.

    Raises:
        HTTPException: If user ID is invalid or user is not found.
    """
    payload_response = verify_access_token(User_Token)

    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")

    try:
        user_id = ObjectId(user_id)
    except Exception:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid user ID format."})

    user_data = await db["users"].find_one({"_id": user_id})
    if not user_data:
        return JSONResponse(status_code=404, content={"status": "error", "message": "User not found."})

    return JSONResponse(
        content={
            "status": "success",
            "message": "User profile fetched successfully.",
            "data": {
                "username": user_data["username"],
                "email": user_data["email"],
                "google_auth": user_data.get("google_auth", False),
                "profile_picture": user_data.get("profile_picture", None),
            },
        }
    )



