"""
PDF Parser Service - Extracts and cleans text from PDF files using PyMuPDF (fitz)
PyMuPDF is faster and more accurate than most PDF extraction libraries.
"""

import re
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract raw text from a PDF provided as bytes.

    Uses PyMuPDF (fitz) to open and iterate over all pages,
    extracting text from each page block by block.

    Args:
        pdf_bytes: Raw bytes of the PDF file (from file.read())

    Returns:
        A single cleaned string containing all text from the PDF
    """
    # Open the PDF from memory bytes (no temp file needed)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    all_text = []

    # Iterate over each page in the document
    for page_num, page in enumerate(doc):
        # Extract text as a plain string (preserves layout hints)
        page_text = page.get_text("text")

        # Add a page separator marker for potential future use
        if page_text.strip():
            all_text.append(f"[Page {page_num + 1}]\n{page_text}")

    # Close the document to free memory
    doc.close()

    # Join all pages and clean the text
    raw_text = "\n\n".join(all_text)
    cleaned_text = clean_text(raw_text)

    return cleaned_text


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text by removing noise, extra whitespace,
    and common PDF artifacts.

    Args:
        text: Raw extracted text string

    Returns:
        Cleaned text string
    """
    # Replace multiple consecutive newlines with a double newline (paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Remove lines that are purely numeric page markers (e.g., "1", "42")
    lines = [line for line in lines if not re.match(r"^\d+$", line.strip())]

    # Rejoin cleaned lines
    text = "\n".join(lines)

    # Remove null bytes and other control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()
