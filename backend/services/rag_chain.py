"""
RAG Chain Service - Retrieval-Augmented Generation pipeline
Retrieves relevant chunks from ChromaDB and generates answers using Google Gemini API.
"""

import os
from typing import Dict, Any, List
import google.generativeai as genai

from services.vector_store import retrieve_chunks

# Configure Gemini API with the key from environment variables
# The key is loaded from .env file via python-dotenv in main.py
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 1.5 Flash for fast and cost-efficient responses
# Switch to "gemini-1.5-pro" for more complex reasoning tasks
GEMINI_MODEL = "gemini-1.5-flash"

# System prompt that instructs Gemini to act as a multilingual document assistant
SYSTEM_PROMPT = """You are BhashaBot, an intelligent multilingual document assistant.
You help users understand PDF documents by answering questions based on the provided context.

Instructions:
- Answer ONLY based on the provided context chunks
- If the answer is not in the context, clearly state that you don't have enough information
- Respond in the SAME LANGUAGE as the user's question
- Be concise but comprehensive
- Cite which part of the document supports your answer when possible
- Do not make up information not present in the context
"""


def build_prompt(query: str, context_chunks: List[str], detected_language: str) -> str:
    """
    Build the full prompt for Gemini by combining context chunks and the user query.

    Args:
        query: The user's question
        context_chunks: List of relevant text chunks from the PDF
        detected_language: The detected language of the query

    Returns:
        Formatted prompt string ready for the Gemini API
    """
    # Format each context chunk with a numbered label
    context_text = "\n\n---\n\n".join(
        [f"[Chunk {i + 1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)]
    )

    # Build the full prompt with context and query
    prompt = f"""The user's question is in {detected_language}.

CONTEXT FROM DOCUMENT:
{context_text}

USER QUESTION: {query}

Please answer the question based on the context provided above.
Respond in {detected_language}."""

    return prompt


def run_rag_chain(
    query: str,
    session_id: str,
    detected_language: str,
) -> Dict[str, Any]:
    """
    Execute the full RAG pipeline:
    1. Retrieve top-5 relevant chunks from ChromaDB
    2. Build a context-enriched prompt
    3. Call Gemini API for answer generation
    4. Return answer with source metadata

    Args:
        query: The user's question string
        session_id: The session ID to scope the ChromaDB search
        detected_language: Detected language of the query (for prompt construction)

    Returns:
        Dict with keys: 'answer' (str), 'sources' (list of source metadata dicts)
    """
    # Step 1: Retrieve the most relevant chunks from ChromaDB
    retrieved = retrieve_chunks(session_id=session_id, query=query)

    if not retrieved:
        return {
            "answer": "I couldn't find any relevant information in the uploaded document. Please make sure a PDF has been uploaded for this session.",
            "sources": [],
        }

    # Extract just the text from retrieved results for the prompt
    context_chunks = [r["text"] for r in retrieved]

    # Build source attribution list for the response
    sources = [
        {
            "filename": r["metadata"].get("filename", "Unknown"),
            "chunk_index": r["metadata"].get("chunk_index", 0),
            "relevance_score": round(1 - r["distance"], 4),  # Convert distance to score
        }
        for r in retrieved
    ]

    # Step 2: Build the Gemini prompt with context
    prompt = build_prompt(query, context_chunks, detected_language)

    # Step 3: Call Gemini API
    try:
        # Initialize the generative model
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )

        # Generate response with safety settings for multilingual content
        response = model.generate_content(
            contents=prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,       # Lower temperature for factual Q&A
                max_output_tokens=1024,
            ),
        )

        answer = response.text

    except Exception as e:
        # Handle API errors gracefully
        answer = f"Error generating response: {str(e)}. Please check your GEMINI_API_KEY."

    return {
        "answer": answer,
        "sources": sources,
    }
