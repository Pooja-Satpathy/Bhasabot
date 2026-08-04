"""
BhashaBot Backend - FastAPI Application Entry Point
Multilingual RAG application supporting Indian and global languages
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import route modules
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from services.database import init_db

# Initialize database tables on startup
init_db()

# Initialize FastAPI app with metadata
app = FastAPI(
    title="BhashaBot API",
    description="Multilingual RAG application for PDF-based question answering",
    version="1.0.0",
)

# Configure CORS to allow requests from the React frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],   # Allow all headers including Authorization
)

# Register route modules with API prefix
app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])



@app.get("/")
async def root():
    """Health check endpoint to verify the API is running."""
    return {"message": "BhashaBot API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
    }
