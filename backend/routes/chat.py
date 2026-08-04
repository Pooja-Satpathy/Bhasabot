"""
Chat Route - Handles user query processing and response generation
Accepts query text and session_id, returns AI-generated answer with sources
"""

from fastapi import APIRouter, HTTPException, Depends
from models.schemas import ChatRequest, ChatResponse
from services.translator import detect_language
from services.rag_chain import run_rag_chain
from services.auth import get_current_user
from services.database import get_session_by_id

# Create a router instance for chat-related endpoints
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a user's query against their uploaded PDF documents.
    Verifies that the user owns the session before processing.
    """
    # Validate that session_id is provided
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required. Please upload a PDF first.",
        )

    # Verify that the session exists and belongs to the authenticated user
    session = get_session_by_id(request.session_id)
    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You do not have access to this document session.",
        )

    # Step 1: Detect the language of the incoming query
    detected_lang = detect_language(request.query)

    # Convert request.history to a list of dictionaries if provided
    history_data = None
    if request.history:
        history_data = [{"role": h.role, "content": h.content} for h in request.history]

    # Step 2: Run the RAG pipeline — retrieve chunks and generate an answer
    result = run_rag_chain(
        query=request.query,
        session_id=request.session_id,
        detected_language=detected_lang,
        history=history_data,
        preferred_language=request.preferred_language,
        tone=request.tone,
    )

    return ChatResponse(
        answer=result["answer"],
        detected_language=detected_lang,
        sources=result.get("sources", []),
        session_id=request.session_id,
    )
