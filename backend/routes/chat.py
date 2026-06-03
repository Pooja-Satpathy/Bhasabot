"""
Chat Route - Handles user query processing and response generation
Accepts query text and session_id, returns AI-generated answer with sources
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.translator import detect_language
from services.rag_chain import run_rag_chain

# Create a router instance for chat-related endpoints
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a user's query against their uploaded PDF documents.

    Steps:
    1. Detect the language of the query
    2. Run the RAG chain (retrieve relevant chunks + generate answer)
    3. Return the answer along with source references and detected language

    Args:
        request: ChatRequest containing query and session_id

    Returns:
        ChatResponse with answer, detected_language, and sources list
    """
    # Validate that session_id is provided
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required. Please upload a PDF first.",
        )

    # Step 1: Detect the language of the incoming query
    detected_lang = detect_language(request.query)

    # Step 2: Run the RAG pipeline — retrieve chunks and generate a Gemini answer
    result = run_rag_chain(
        query=request.query,
        session_id=request.session_id,
        detected_language=detected_lang,
    )

    return ChatResponse(
        answer=result["answer"],
        detected_language=detected_lang,
        sources=result.get("sources", []),
        session_id=request.session_id,
    )
