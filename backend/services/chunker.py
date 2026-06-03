"""
Chunker Service - Splits long text into overlapping token-based chunks
Uses a 500-token window with 50-token overlap to preserve context at boundaries.
"""

from typing import List


# Approximate characters per token for multilingual text (conservative estimate)
# For proper token counting, you could use tiktoken or a HuggingFace tokenizer
CHARS_PER_TOKEN = 4

CHUNK_SIZE_TOKENS = 500     # Target size of each chunk in tokens
OVERLAP_TOKENS = 50         # Overlap between consecutive chunks in tokens

# Convert token counts to character counts for splitting
CHUNK_SIZE_CHARS = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN    # 2000 chars
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN          # 200 chars


def chunk_text(text: str) -> List[str]:
    """
    Split a long text string into overlapping chunks.

    Uses a sliding window approach:
    - Each chunk is approximately CHUNK_SIZE_TOKENS tokens
    - Consecutive chunks overlap by OVERLAP_TOKENS tokens
    - Splits are attempted at sentence/paragraph boundaries for cleaner chunks

    Args:
        text: The full extracted text from a PDF

    Returns:
        A list of text chunk strings
    """
    # First, split text into sentences/paragraphs for cleaner boundaries
    paragraphs = split_into_paragraphs(text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk and start new one
        if len(current_chunk) + len(paragraph) > CHUNK_SIZE_CHARS and current_chunk:
            # Save the completed chunk
            chunks.append(current_chunk.strip())

            # Start new chunk with overlap — take the last OVERLAP_CHARS characters
            # of the previous chunk to maintain context continuity
            current_chunk = current_chunk[-OVERLAP_CHARS:] + "\n" + paragraph
        else:
            # Append paragraph to current chunk
            current_chunk += "\n" + paragraph if current_chunk else paragraph

    # Don't forget the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Filter out empty or too-short chunks (less than 50 chars)
    chunks = [c for c in chunks if len(c) > 50]

    return chunks


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into logical paragraphs.
    Tries to preserve semantic units for better chunking quality.

    Args:
        text: Full document text

    Returns:
        List of paragraph strings
    """
    # Split on double newlines (paragraph breaks)
    paragraphs = [p.strip() for p in text.split("\n\n")]

    # Filter out empty paragraphs
    paragraphs = [p for p in paragraphs if p]

    return paragraphs
