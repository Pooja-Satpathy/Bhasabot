"""
Models and Pydantic Schemas for BhashaBot API
Defines request and response shapes for type safety and auto-documentation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Upload Endpoint Schemas
# ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response returned after successful PDF upload and processing."""

    session_id: str = Field(
        ...,
        description="Unique identifier for this upload session. Use in chat requests.",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    )
    filename: str = Field(
        ...,
        description="Original name of the uploaded PDF file.",
        example="report.pdf",
    )
    chunks_stored: int = Field(
        ...,
        description="Number of text chunks extracted and stored in the vector database.",
        example=42,
    )
    message: str = Field(
        ...,
        description="Human-readable upload status message.",
        example="Successfully processed 'report.pdf' into 42 chunks.",
    )
    duplicate: bool = Field(
        default=False,
        description="Whether identical document bytes are already indexed for this user.",
    )
    document_version: int = Field(
        default=1,
        ge=1,
        description="Processing version of this document for the current user.",
    )


# ─────────────────────────────────────────────
# Chat Endpoint Schemas
# ─────────────────────────────────────────────

class MessageParam(BaseModel):
    """A single message representing a turn in chat history."""

    role: str = Field(..., description="The role of the speaker, either 'user' or 'bot'.")
    content: str = Field(..., description="The text content of the message.")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question in any supported language.",
        example="What are the main findings of this report?",
    )
    session_id: str = Field(
        ...,
        description="Session ID from the upload response. Scopes the search to your document.",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    )
    history: Optional[List[MessageParam]] = Field(
        default=None,
        description="Optional list of previous messages in the session to maintain conversational memory.",
    )
    preferred_language: Optional[str] = Field(
        default="Auto Detect",
        description="Optional sidebar language preference. One of: Auto Detect, English, Hindi, Odia, Hinglish, Odilish.",
    )
    tone: Optional[str] = Field(
        default="Friendly",
        description="Optional response tone. One of: Professional, Friendly, Simple.",
    )


class SourceReference(BaseModel):
    """Metadata about a retrieved source chunk used in generating the answer."""

    filename: str = Field(..., description="Name of the source PDF file.")
    chunk_index: int = Field(..., description="Index of the chunk within the document.")
    relevance_score: float = Field(
        ...,
        description="Relevance score (0-1) where 1 is most relevant.",
        ge=0.0,
        le=1.0,
    )


class ChatResponse(BaseModel):
    """Response returned after processing a chat query."""

    answer: str = Field(
        ...,
        description="The AI-generated answer based on the document content.",
    )
    detected_language: str = Field(
        ...,
        description="The detected language of the user's query.",
        example="Hindi",
    )
    sources: List[SourceReference] = Field(
        default=[],
        description="List of source chunks used to generate the answer.",
    )
    session_id: str = Field(
        ...,
        description="The session ID associated with this conversation.",
    )


# ─────────────────────────────────────────────
# Error Schema
# ─────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str = Field(..., description="Human-readable error description.")
    error_code: Optional[str] = Field(None, description="Machine-readable error code.")


# ─────────────────────────────────────────────
# Auth Endpoint Schemas
# ─────────────────────────────────────────────

class UserCredentials(BaseModel):
    """Request schema for login containing username (or email) and password."""
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=6, max_length=100, description="Plaintext password")


class AuthResponse(BaseModel):
    """Response returned upon successful login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type prefix")
    username: str = Field(..., description="Authenticated user's username")
    email: str = Field(..., description="Authenticated user's email")


class UserProfile(BaseModel):
    """User profile information."""
    id: int = Field(..., description="Unique database user ID")
    username: str = Field(..., description="The user's username")
    email: str = Field(..., description="The user's email")




class SessionDetail(BaseModel):
    """Details of a saved document upload session."""
    session_id: str = Field(..., description="Session ID identifier")
    filename: str = Field(..., description="Uploaded PDF filename")
    chunks_stored: int = Field(..., description="Chunks generated from the PDF")
    document_version: int = Field(default=1, description="Document processing version")
    created_at: str = Field(..., description="Timestamp of creation")

