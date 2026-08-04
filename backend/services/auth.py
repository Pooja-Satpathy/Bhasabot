"""
Authentication Service - Password hashing and JWT token handling
Provides secure password hashing (PBKDF2) and base64-based JWT creation/verification.
"""

import os
import base64
import json
import hmac
import hashlib
import time
import secrets
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.database import get_user_by_id

# Secret key and algorithm configuration (loaded from environment)
JWT_SECRET = os.getenv("JWT_SECRET", "bhashabot_super_secret_jwt_key_2026_dev")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_SECONDS = 86400  # Token valid for 24 hours

security = HTTPBearer()


# ──────────────────────────────────────────────────────────────────────────────
# Password Hashing Logic (PBKDF2-HMAC-SHA256)
# ──────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a unique salt.
    Format returned: salt$hash_hex
    """
    salt = secrets.token_hex(16)
    # Perform 100k rounds of PBKDF2
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    )
    return f"{salt}${key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against the stored salt$hash_hex.
    """
    try:
        if not hashed_password or "$" not in hashed_password:
            return False
        salt, key_hex = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# JSON Web Token (JWT) Encoder/Decoder
# ──────────────────────────────────────────────────────────────────────────────

def base64url_encode(data: bytes) -> str:
    """Encode bytes to Base64URL string (no padding, url-safe)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64url_decode(data: str) -> bytes:
    """Decode Base64URL string to bytes."""
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Create a signed JWT token.

    Args:
        data: The claims to include in the payload
        expires_delta: Optional lifetime in seconds (default is 24 hours)

    Returns:
        Signed JWT string in header.payload.signature format
    """
    to_encode = data.copy()
    expire_time = time.time() + (expires_delta or TOKEN_EXPIRE_SECONDS)
    to_encode.update({"exp": expire_time})

    # Header
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    header_b64 = base64url_encode(header_json)

    # Payload
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64url_encode(payload_json)

    # Signature
    signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature_bytes = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signature_input,
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature_bytes)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a signed JWT token.

    Raises ValueError if token format, signature, or expiration is invalid.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, signature_b64 = parts

    # Recreate signature to verify authenticity
    signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature_bytes = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signature_input,
        hashlib.sha256
    ).digest()
    expected_signature_b64 = base64url_encode(expected_signature_bytes)

    if not hmac.compare_digest(signature_b64, expected_signature_b64):
        raise ValueError("Signature validation failed")

    # Decode payload
    payload_bytes = base64url_decode(payload_b64)
    payload = json.loads(payload_bytes.decode("utf-8"))

    # Check expiration claim
    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("Token has expired")

    return payload


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Dependency for Endpoint Protection
# ──────────────────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and authenticate the JWT from requests.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: Missing identifier (sub)",
            )
        
        user = get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: User no longer exists",
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
