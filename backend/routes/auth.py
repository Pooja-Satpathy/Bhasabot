"""
Auth Route - Handles user signup, login, profile check, and session history list
"""

import re
from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from models.schemas import UserCredentials, AuthResponse, UserProfile, SessionDetail
from services.database import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    get_user_sessions,
    delete_user_session
)
from services.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


class UserSignup(BaseModel):
    """Request schema for user registration containing username, email and passwords."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, max_length=100, description="Plaintext password")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="Confirm password field")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(credentials: UserSignup):
    """
    Register a new user and prompt them to log in.
    """
    # 1. Validate username format (alphanumeric and underscores only)
    username = credentials.username.strip()
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can only contain letters, numbers, and underscores"
        )

    # 2. Validate email format
    email = credentials.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # 3. Validate passwords match
    if credentials.password != credentials.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # 4. Create user in SQLite
    try:
        hashed = hash_password(credentials.password)
        create_user(username, email, hashed)
        
        # Return success response (does NOT return a JWT, forcing user to log in)
        return {
            "message": "User registered successfully. Please log in.",
            "username": username,
            "email": email
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserCredentials):
    """
    Authenticate user credentials (username or email) and return a JWT access token.
    """
    login_id = credentials.username.strip()
    
    # Try finding user by username first, fallback to email
    user = get_user_by_username(login_id)
    if not user:
        user = get_user_by_email(login_id)
        
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store sub (user id), username, and email in payload
    token = create_access_token({
        "sub": user["id"],
        "username": user["username"],
        "email": user["email"]
    })
    return AuthResponse(
        access_token=token,
        username=user["username"],
        email=user["email"]
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Return the profile of the currently logged-in user.
    """
    return UserProfile(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"]
    )


@router.get("/sessions", response_model=List[SessionDetail])
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """
    Retrieve document session history for the current user.
    """
    sessions = get_user_sessions(current_user["id"])
    return [
        SessionDetail(
            session_id=s["session_id"],
            filename=s["filename"],
            chunks_stored=s["chunks_stored"],
            document_version=s["document_version"],
            created_at=str(s["created_at"])
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Remove a document session index from the user's history list.
    """
    success = delete_user_session(session_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or not owned by you"
        )
    return {"message": "Session deleted from history successfully"}
