"""
Embedder Service - Generates multilingual sentence embeddings
Uses 'intfloat/multilingual-e5-large' from HuggingFace via sentence-transformers.
This model supports 100+ languages including Hindi, Tamil, Telugu, Bengali, etc.
"""

import os
from typing import List
from sentence_transformers import SentenceTransformer

# Force ALL HuggingFace/PyTorch caches to D drive
# This must be set before any model loading happens
MODEL_CACHE_DIR = "D:\\bhashabot\\backend\\hf_cache"
os.environ["HF_HOME"] = MODEL_CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = MODEL_CACHE_DIR
os.environ["SENTENCE_TRANSFORMERS_HOME"] = MODEL_CACHE_DIR
os.environ["TORCH_HOME"] = MODEL_CACHE_DIR

# Model name — multilingual-e5-large supports 100+ languages including all Indian languages
# Already downloaded to D:\bhashabot\backend\hf_cache\ — no re-download needed!
MODEL_NAME = "intfloat/multilingual-e5-small"

# Load the model once at module level to avoid reloading on every request
# This is cached in memory for the lifetime of the FastAPI process
_model: SentenceTransformer = None


def get_model() -> SentenceTransformer:
    """
    Lazy-load and cache the SentenceTransformer model.
    Downloads the model on first call (~560MB), then uses cache.

    Returns:
        Loaded SentenceTransformer model instance
    """
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME} ...")
        print(f"Cache directory: {MODEL_CACHE_DIR}")
        # Pass cache_folder explicitly to guarantee D drive usage
        _model = SentenceTransformer(MODEL_NAME, cache_folder=MODEL_CACHE_DIR)
        print("Embedding model loaded successfully.")
    return _model


def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings for a list of text chunks.

    The multilingual-e5-large model requires a 'passage: ' prefix
    for document chunks and 'query: ' prefix for queries (per model docs).

    Args:
        chunks: List of text chunks to embed

    Returns:
        List of embedding vectors (each a list of 1024 floats)
    """
    if not chunks:
        return []
        
    model = get_model()

    # Prefix each chunk with 'passage: ' as required by E5 models for documents
    prefixed_chunks = [f"passage: {chunk}" for chunk in chunks]

    # Generate embeddings — normalize_embeddings=True gives unit vectors
    # which improves cosine similarity search quality
    embeddings = model.encode(
        prefixed_chunks,
        normalize_embeddings=True,
        show_progress_bar=True,   # Show progress for large documents
        batch_size=10,            # Process in batches to manage memory
    )

    # Convert numpy arrays to plain Python lists for JSON serialization
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Generate an embedding for a single search query.
    Uses 'query: ' prefix as required by E5 models for queries.

    Args:
        query: The user's search query string

    Returns:
        Embedding vector as a list of floats
    """
    model = get_model()

    # Prefix with 'query: ' for retrieval queries (E5 model convention)
    prefixed_query = f"query: {query}"

    # Encode single query and return as a flat list
    embedding = model.encode(
        prefixed_query,
        normalize_embeddings=True,
    )

    return embedding.tolist()
