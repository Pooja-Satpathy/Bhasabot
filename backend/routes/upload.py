"""
Upload Route - Handles PDF file upload and ingestion into ChromaDB
Accepts multipart/form-data with a PDF file and optional session_id
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from services.pdf_parser import extract_text_from_pdf
from services.chunker import chunk_text
from services.embedder import generate_embeddings
from services.vector_store import store_chunks
from models.schemas import UploadResponse

# Create a router instance for upload-related endpoints
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),              # The PDF file to upload
    session_id: str = Form(default=None),      # Optional session identifier
):
    """
    Upload a PDF file, extract its text, chunk it, embed it,
    and store the vectors in ChromaDB for later retrieval.

    Args:
        file: The uploaded PDF file (must be application/pdf)
        session_id: Optional session ID to scope the document

    Returns:
        UploadResponse with session_id, filename, and chunk count
    """
    # Validate that the uploaded file is a PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Generate a new session_id if one was not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Read raw bytes from the uploaded file
    pdf_bytes = await file.read()

    # Step 1: Extract clean text from the PDF using PyMuPDF
    extracted_text = extract_text_from_pdf(pdf_bytes)

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the PDF.")

    # Step 2: Split the extracted text into overlapping chunks
    chunks = chunk_text(extracted_text)

    # Step 3: Generate multilingual embeddings for each chunk
    embeddings = generate_embeddings(chunks)

    # Step 4: Store chunks and their embeddings in ChromaDB
    store_chunks(
        session_id=session_id,
        chunks=chunks,
        embeddings=embeddings,
        filename=file.filename,
    )

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        chunks_stored=len(chunks),
        message=f"Successfully processed '{file.filename}' into {len(chunks)} chunks.",
    )
