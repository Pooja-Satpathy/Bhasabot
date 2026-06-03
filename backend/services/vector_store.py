"""
Vector Store Service - ChromaDB setup, storage, and retrieval of document chunks
ChromaDB is an open-source embedding database that runs locally.
"""

import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

from services.embedder import embed_query

# Directory where ChromaDB will persist its data on disk
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# Number of top chunks to retrieve for each query
TOP_K = 5

# Initialize ChromaDB client with persistent storage
# This creates a local SQLite-based vector store that survives restarts
_client: chromadb.PersistentClient = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create the ChromaDB persistent client.
    Uses lazy initialization to avoid startup overhead.

    Returns:
        ChromaDB PersistentClient instance
    """
    global _client
    if _client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_collection(session_id: str):
    """
    Get or create a ChromaDB collection scoped to a session.
    Each upload session gets its own collection to avoid cross-contamination.

    Args:
        session_id: Unique identifier for the upload session

    Returns:
        ChromaDB Collection object
    """
    client = get_chroma_client()

    # Collection name must be valid: alphanumeric and hyphens only
    # Replace underscores and other chars for ChromaDB compatibility
    collection_name = f"session_{session_id.replace('-', '_')}"

    # get_or_create_collection ensures idempotency
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},  # Use cosine similarity for E5 embeddings
    )

    return collection


def store_chunks(
    session_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
    filename: str,
) -> None:
    """
    Store text chunks and their embeddings in ChromaDB.

    Args:
        session_id: The upload session identifier
        chunks: List of text chunk strings
        embeddings: Corresponding list of embedding vectors
        filename: Original PDF filename (stored as metadata)
    """
    collection = get_collection(session_id)

    # Create unique IDs for each chunk using session_id and index
    ids = [f"{session_id}_chunk_{i}" for i in range(len(chunks))]

    # Build metadata for each chunk — useful for source attribution
    metadatas = [
        {
            "filename": filename,
            "chunk_index": i,
            "session_id": session_id,
        }
        for i in range(len(chunks))
    ]

    # Upsert all chunks at once (efficient batch operation)
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Stored {len(chunks)} chunks in collection '{collection.name}'")


def retrieve_chunks(session_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Retrieve the top-K most semantically similar chunks for a query.

    Args:
        session_id: The upload session to search within
        query: The user's query string

    Returns:
        List of result dicts with keys: 'text', 'metadata', 'distance'
    """
    collection = get_collection(session_id)

    # Generate embedding for the query (with 'query: ' prefix for E5)
    query_embedding = embed_query(query)

    # Query ChromaDB for the top-K nearest neighbors
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(TOP_K, collection.count()),  # Don't request more than available
        include=["documents", "metadatas", "distances"],
    )

    # Flatten the nested result structure into a clean list
    retrieved = []
    for i, doc in enumerate(results["documents"][0]):
        retrieved.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return retrieved
