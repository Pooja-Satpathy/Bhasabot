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
        description="Human-readable success message.",
        example="Successfully processed 'report.pdf' into 42 chunks.",
    )


# ─────────────────────────────────────────────
# Chat Endpoint Schemas
# ─────────────────────────────────────────────

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
