"""
Upload Route - Handles PDF file upload and ingestion into ChromaDB
Accepts multipart/form-data with a PDF file and optional session_id
"""

import hashlib
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from services.pdf_parser import extract_text_from_pdf
from services.chunker import chunk_text
from services.embedder import generate_embeddings
from services.vector_store import store_chunks
from services.auth import get_current_user
from services.database import (
    get_legacy_session_by_filename,
    get_next_document_version,
    get_session_by_hash,
    save_user_session,
)
from models.schemas import UploadResponse

# Create a router instance for upload-related endpoints
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),              # The PDF file to upload
    session_id: str = Form(default=None),      # Optional session identifier
    force_reprocess: bool = Form(default=False),
    current_user: dict = Depends(get_current_user), # Requires user login
):
    """
    Upload a PDF file, extract its text, chunk it, embed it,
    and store the vectors in ChromaDB for later retrieval.
    Linked to the currently authenticated user.
    """
    # Validate that the uploaded file is a PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Read once so identical files can be detected before expensive processing.
    pdf_bytes = await file.read()
    file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    if not force_reprocess:
        existing = get_session_by_hash(current_user["id"], file_hash)
        duplicate_message = "This exact PDF is already indexed."

        # Sessions created before file hashing can only be compared by filename.
        if not existing:
            existing = get_legacy_session_by_filename(
                current_user["id"], file.filename
            )
            duplicate_message = "A previously indexed PDF has the same filename."

        if existing:
            return UploadResponse(
                session_id=existing["session_id"],
                filename=existing["filename"],
                chunks_stored=existing["chunks_stored"],
                message=f"{duplicate_message} Use it or process the upload again.",
                duplicate=True,
                document_version=existing["document_version"],
            )

    # A forced reprocess always receives a new isolated vector collection.
    if not session_id or force_reprocess:
        session_id = str(uuid.uuid4())

    document_version = get_next_document_version(
        current_user["id"], file_hash, file.filename
    )

    # Step 1: Extract clean text from the PDF using PyMuPDF
    extracted_text = extract_text_from_pdf(pdf_bytes)

    if not extracted_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from the PDF.")

    # Step 2: Split the extracted text into overlapping chunks
    chunks = chunk_text(extracted_text)

    # Process in batches to prevent memory exhaustion and crashing
    BATCH_SIZE = 10 
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        
        # Step 3: Generate multilingual embeddings for this batch
        batch_embeddings = generate_embeddings(batch_chunks)
        
        # Step 4: Store batch in ChromaDB
        store_chunks(
            session_id=session_id,
            chunks=batch_chunks,
            embeddings=batch_embeddings,
            filename=file.filename,
            start_index=i
        )

    # Step 5: Save session association in database for history lookup
    save_user_session(
        session_id=session_id,
        user_id=current_user["id"],
        filename=file.filename,
        chunks_stored=len(chunks),
        file_hash=file_hash,
        document_version=document_version,
    )

    return UploadResponse(
        session_id=session_id,
        filename=file.filename,
        chunks_stored=len(chunks),
        message=f"Successfully processed '{file.filename}' into {len(chunks)} chunks.",
        duplicate=False,
        document_version=document_version,
    )
